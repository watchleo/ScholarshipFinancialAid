"""Start the scholarship HTTP server with python app.py."""

import argparse

import uvicorn

from api import create_app
from config import SETTINGS
from database import db


def main():
    parser = argparse.ArgumentParser(description="Scholarship and Financial Aid API")
    parser.add_argument("--host", default=SETTINGS["host"])
    parser.add_argument("--port", type=int, default=SETTINGS["port"])
    parser.add_argument("--debug", action="store_true", default=SETTINGS["debug"],
                        help="use verbose server logging")
    parser.add_argument("--reset-db", action="store_true",
                        help="delete the current database and restore the sample records")
    parser.add_argument("--init-only", action="store_true",
                        help="prepare the database and exit")
    args = parser.parse_args()
    if args.reset_db:
        db.reset_db()
    if args.init_only:
        if not args.reset_db:
            db.init_db()
        print(f"Database ready at {db.get_db_path()}")
        return
    uvicorn.run(create_app(), host=args.host, port=args.port,
                log_level="debug" if args.debug else "info")


if __name__ == "__main__":
    main()
