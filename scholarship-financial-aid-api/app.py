"""Scholarship and Financial Aid Management System - HTTP API server.

This is the entry point of the application (Unit III: HTTP API Server).
Run it from the project root - NO virtual environment required:

    python app.py                  start the server on 127.0.0.1:5000
    python app.py --port 5001      use another port
    python app.py --reset-db       wipe + recreate + reseed the database
    python app.py --init-only      just prepare the database, then exit

It also runs fine inside IDLE (open this file, press F5).
"""

import argparse

from api import create_app
from config import SETTINGS
from database import db
from utils import app_logger


def parse_arguments():
    """Command-line options (argparse module)."""
    parser = argparse.ArgumentParser(
        description="Scholarship and Financial Aid Management System - "
                    "REST API server (Flask + SQLite)")
    parser.add_argument("--host", default=SETTINGS["host"],
                        help="interface to bind (default: %(default)s)")
    parser.add_argument("--port", type=int, default=SETTINGS["port"],
                        help="TCP port (default: %(default)s)")
    parser.add_argument("--debug", action="store_true",
                        default=SETTINGS.get("debug", False),
                        help="run Flask in debug mode")
    parser.add_argument("--reset-db", action="store_true",
                        help="delete, recreate and reseed the database "
                             "before starting")
    parser.add_argument("--init-only", action="store_true",
                        help="only initialize the database, then exit")
    return parser.parse_args()


def print_banner(args):
    """Startup summary printed to the console."""
    line = "=" * 68
    print(line)
    print(" Scholarship and Financial Aid Management System - REST API")
    print(" HTTP API Server (Flask) + SQLite | Group 5 case study (3NF)")
    print(line)
    print(f" API base     : http://{args.host}:{args.port}/api")
    print(f" Health check : http://{args.host}:{args.port}/api/health")
    print(f" Database     : {db.get_db_path()}")
    print(f" Log file     : {SETTINGS['log_path']}")
    print(" Demo client  : python demo.py    (run in a second terminal)")
    print(" Stop server  : Ctrl+C")
    print(line)


def main():
    args = parse_arguments()
    logger = app_logger.get_logger("main")

    if args.reset_db:
        db.reset_db()
        logger.warning("Database was reset and reseeded (--reset-db).")

    app = create_app()

    if args.init_only:
        logger.info("Database initialized. Exiting (--init-only).")
        print("Database initialized and seeded. You can now start the "
              "server with:  python app.py")
        return

    print_banner(args)
    # Flask's built-in development HTTP server (Werkzeug)
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
