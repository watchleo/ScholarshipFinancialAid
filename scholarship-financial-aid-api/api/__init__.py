"""HTTP API layer (Unit III: HTTP API Server + GET/POST + REST API).

This package turns the service layer into a REST API:

* every endpoint speaks JSON in and JSON out;
* GET reads, POST creates or triggers actions, PUT updates, DELETE removes
  (REST conventions over clean resource URLs);
* errors always come back as JSON with the correct HTTP status code
  (400 / 404 / 409 / 422 / 500).
"""

import time
from datetime import datetime
from pathlib import Path

import sqlite3
from flask import Flask, g, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from config import ensure_runtime_dirs
from database import db
from utils import app_logger
from utils.exceptions import AppError

from .applications import applications_bp
from .catalog import catalog_bp
from .reports import reports_bp
from .scholarships import scholarships_bp
from .students import students_bp


def create_app(db_path=None, seed=True):
    """Application factory: build a fully configured Flask app.

    ``db_path`` lets the automated tests run against a throwaway database.
    """
    if db_path:
        db.configure_database(db_path)
    ensure_runtime_dirs()

    logger = app_logger.get_logger("startup")
    db.init_db(seed=seed)
    logger.info("Database ready at %s", db.get_db_path())

    app = Flask(__name__, static_folder="static/assets", static_url_path="/assets")
    app.url_map.strict_slashes = False   # /api/students/ also works
    app.json.sort_keys = False           # keep our field order in responses

    _register_error_handlers(app)
    _register_request_logging(app)
    _register_root_routes(app)

    app.register_blueprint(students_bp)
    app.register_blueprint(scholarships_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(reports_bp)

    logger.info("API ready with %d routes", len(list(app.url_map.iter_rules())))
    return app


def _register_root_routes(app):
    """Landing page + health check."""

    @app.get("/")
    def index():
        index_path = Path(app.root_path) / "static" / "index.html"
        if not index_path.is_file():
            return (
                "Ionic frontend is not built. Run `npm ci && npm run build` "
                "from the frontend directory.",
                503,
            )
        return send_from_directory(index_path.parent, index_path.name)

    @app.get("/api/health")
    def health():
        """Liveness probe: also proves the database is reachable."""
        counts = db.table_row_counts()
        return jsonify({
            "status": "ok",
            "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "database": db.get_db_path(),
            "total_records": sum(counts.values()),
            "tables": counts,
        })


def _register_request_logging(app):
    """Log every request with method, path, status code and duration."""
    access_logger = app_logger.get_logger("http")

    @app.before_request
    def _start_timer():
        g.started_at = time.perf_counter()

    @app.after_request
    def _log_request(response):
        started = g.get("started_at", time.perf_counter())
        duration_ms = (time.perf_counter() - started) * 1000
        access_logger.info("%-6s %s -> %d (%.1f ms)",
                           request.method, request.path,
                           response.status_code, duration_ms)
        return response


def _register_error_handlers(app):
    """Convert every error into a consistent JSON body."""

    @app.errorhandler(AppError)
    def _handle_app_error(error):
        # Domain errors raised by the service layer
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(HTTPException)
    def _handle_http_exception(error):
        # Flask/Werkzeug errors (404 unknown route, 405 wrong method, ...)
        code = error.name.lower().replace(" ", "_")
        return jsonify({"error": {"code": code, "message": error.description}}), \
            error.code or 500

    @app.errorhandler(sqlite3.IntegrityError)
    def _handle_integrity_error(error):
        return jsonify({"error": {
            "code": "conflict",
            "message": "Database constraint violated - the record may be "
                       "duplicated or still referenced.",
            "details": {"reason": str(error)},
        }}), 409

    @app.errorhandler(Exception)
    def _handle_unexpected_error(error):
        # Anything unexpected: log the full traceback, return a clean 500
        app_logger.get_logger("errors").exception("Unhandled error: %s", error)
        return jsonify({"error": {
            "code": "internal_error",
            "message": "An unexpected error occurred. "
                       "Check logs/app.log for details.",
        }}), 500
