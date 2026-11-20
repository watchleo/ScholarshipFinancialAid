"""FastAPI application factory, shared handlers and frontend routes."""

import sqlite3
from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from config import BASE_DIR, ensure_runtime_dirs
from database import db
from utils.app_logger import get_logger
from utils.exceptions import AppError

from . import applications, catalog, reports, scholarships, students
from .common import require_api_key


def create_app(db_path=None, seed=True):
    """Initialize the database and assemble the HTTP server."""
    if db_path is not None:
        db.configure_database(db_path)
    ensure_runtime_dirs()
    db.init_db(seed=seed)

    app = FastAPI(
        title="Scholarship and Financial Aid API",
        description="Manage scholarship programs, student applications and awards. "
                    "Use Authorize to send your X-API-Key with each request.",
        version="1.0",
    )
    register_error_handlers(app)
    resources = APIRouter(
        dependencies=[Depends(require_api_key)],
        responses={401: {"description": "Missing or invalid API key"}},
    )

    @resources.get("/api/health", tags=["Server"])
    def health():
        """Check the database connection and count the records in each table."""
        counts = db.table_row_counts()
        return {
            "status": "ok",
            "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "database": db.get_db_path(),
            "total_records": sum(counts.values()),
            "tables": counts,
        }

    for module in (students, scholarships, applications, catalog, reports):
        resources.include_router(module.router)
    app.include_router(resources)

    frontend = BASE_DIR / "frontend"

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(frontend / "index.html")

    app.mount("/assets", StaticFiles(directory=frontend / "assets"), name="assets")
    return app


def register_error_handlers(app):
    @app.exception_handler(AppError)
    async def domain_error(request: Request, error: AppError):
        return JSONResponse(error.to_dict(), status_code=error.status_code)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException):
        code = HTTPStatus(error.status_code).phrase.lower().replace(" ", "_")
        return JSONResponse(
            {"error": {"code": code, "message": error.detail}},
            status_code=error.status_code,
            headers=error.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError):
        issues = error.errors()
        if any(issue["type"] == "json_invalid" for issue in issues):
            return JSONResponse(
                {"error": {"code": "bad_request", "message": "Request body must be valid JSON."}},
                status_code=400,
            )
        fields = {".".join(map(str, issue["loc"])): issue["msg"] for issue in issues}
        return JSONResponse(
            {"error": {"code": "validation_failed", "message": "Invalid request.",
                       "details": {"fields": fields}}},
            status_code=422,
        )

    @app.exception_handler(sqlite3.IntegrityError)
    async def integrity_error(request: Request, error: sqlite3.IntegrityError):
        return JSONResponse(
            {"error": {"code": "conflict", "message": "Database constraint violated.",
                       "details": {"reason": str(error)}}},
            status_code=409,
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, error: Exception):
        get_logger("errors").exception("Unhandled error on %s", request.url.path)
        return JSONResponse(
            {"error": {"code": "internal_error", "message": "An unexpected error occurred."}},
            status_code=500,
        )
