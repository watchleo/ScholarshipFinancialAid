# Unit II Concept Map — where every syllabus topic lives in this project

Requirement from the TO-DO: *"kasama lahat ng nandito sa maliban lang sa
Virtual Environment"* — include every Unit II topic **except the Virtual
Environment**. The table below shows exactly where each topic is used, so you
can point to real code during the defense.

## Unit II — Rudimentary Python Programming

| # | Syllabus topic | Where it is used (file → what to show) |
|---|----------------|----------------------------------------|
| 1 | **Python Programming Language and IDLE** | The whole project is pure Python 3. Run it with `python app.py`, or open `app.py` in **IDLE** and press F5. |
| 2 | **Basic Python Syntax, Comments, Variables, Operators, Data Types** | Every file has a module docstring + comments. Data types in one place: `database/seed_data.py` (str, int, float, None in every row tuple). Arithmetic operators: `services/report_service.py` (`remaining = budget - committed`, `committed / budget * 100`). |
| 3 | **Relational, Equality, and Logical Operators** | `services/eligibility_service.py` → `_evaluate()`: `gpa <= limit` (relational), `== None` checks (equality), `gpa_ok and income_ok` (logical). Also `utils/validators.py` → `clean_gpa()` uses `1.0 <= gpa <= 5.0`, `clean_choice()` uses `not in`. |
| 4 | **Control Flow: Conditionals and Loops** | `if / elif / else`: `services/application_service.py` → `review_application()` (approve vs reject branches). `for` loops: `services/report_service.py` → every report builds rows in a loop. `while` loop: `utils/formatters.py` → `next_sequential_id()` skips already-taken IDs. |
| 5 | **Built-in Data Structures** | **list**: `database/seed_data.py` (one list of tuples per table); `dict`: `services/base_service.py` → `TABLE_REGISTRY` (dict of dicts) and every JSON response; **tuple**: `utils/validators.py` → `APPLICATION_STATUSES`, `PAYMENT_METHODS`; **set**: `utils/formatters.py` → `taken = set(existing_ids)`; **dict comprehension**: `services/application_service.py` → `_requirement_summary()` (`{row["Requirement_Status"]: row["n"] for row in rows}`). |
| 6 | **String Manipulations** | `utils/validators.py`: `.strip()`, `.lower()`, `.replace(",", "")`, `re.fullmatch()`, `", ".join(options)`, `str.upper()`. `utils/formatters.py`: f-string money formatting `f"{amount:,.2f}"` and `.zfill()` for zero-padded IDs. |
| 7 | **Functions** | The whole codebase is function-based. Best examples: `utils/validators.py` (small "cleaner" functions, one job each, parameters + return values), `_validate_entity()` (shared generic loop), and default arguments like `def export_to_file(entity, rows, file_format="csv")`. |
| 8 | **Modules** | Imports everywhere: standard modules `sqlite3, json, csv, re, os, logging, argparse, datetime, time, tempfile, unittest, urllib` + project modules (`from database import db`). `app.py` shows `argparse` (command-line flags); `demo.py` shows `urllib` (HTTP client) and `json`. |
| 9 | **Packages** | Four packages with `__init__.py`: `database/`, `services/`, `api/`, `utils/` — imported like `from services import application_service`. `api/__init__.py` is the application factory. |
| 10 | **Exceptions** | Custom hierarchy in `utils/exceptions.py` (`AppError` → `NotFoundError`, `ValidationError`, `ConflictError`, `BusinessRuleError`, `BadRequestError`). `try/except/finally` in `database/db.py` → `get_db()` (commit / rollback / close). `raise ... from` in `utils/validators.py` → `clean_number()`. Global handlers in `api/__init__.py` convert any error to JSON. `demo.py` catches `HTTPError` / `URLError`. |
| 11 | **File Management** | Read: `config.py` reads `config.json`, `database/db.py` reads `schema.sql` (both with `with open(...)` context managers). Write: `utils/app_logger.py` appends to `logs/app.log`; `utils/exporters.py` writes CSV/JSON files to `data/exports/` and lists them with `os.listdir()`. Delete: `database/db.py` → `init_db(force=True)` uses `os.remove()`. |
| 12 | ~~Virtual Environment~~ | **Excluded per the TO-DO.** The project runs without one — the only install is `pip install -r requirements.txt` (Flask). `requirements.txt` documents this. |

## Unit III — Data Exchange using API (the 3 chosen topics)

| # | Chosen topic | Where it is used |
|---|--------------|------------------|
| 1 | **HTTP API Server** | `app.py` boots the Flask (Werkzeug) HTTP server; `api/__init__.py` → `create_app()` builds the app, registers 61 routes, logs every request (method, path, status, duration) to console + file. |
| 2 | **HTTP GET and POST request** | GET = read (`@bp.get`), POST = create/act (`@bp.post`) — see every module in `api/`. `demo.py` performs raw GET/POST/PUT/DELETE with `urllib.request`, showing the HTTP side explicitly. |
| 3 | **REST API** | Resource-oriented URLs (`/api/students/A001`), JSON bodies, correct status codes (200/201/400/404/409/422/500), nested resources (`/api/applications/A001/disbursements`), stateless request handling. |

*(FastAPI was crossed out in the syllabus and PHP Web API does not apply to a
Python app; API Authentication was not among the chosen three — a possible
extension is sketched at the end of README.md.)*

## Defense talking points (30-second demos)

1. **Run the server** → `python app.py`, open `http://127.0.0.1:5000/api/health`
   in a browser: JSON with row counts of all 10 tables.
2. **Run the demo** → `python demo.py`: the full lifecycle in 18 steps,
   including a validation error (422), a blocked approval, the overshoot
   warning, and a blocked delete (409) — proves exceptions + business rules.
3. **Show the log file** → open `logs/app.log`: every request is on record
   (file management + logging module).
4. **Show an export** → after the demo, open `data/exports/applications_*.csv`
   in Excel (CSV writing with context managers).
5. **Run the tests** → `python -m unittest discover -s tests -v` — 21 green
   tests, including a full approve → disburse → renew workflow.
6. **Point at the schema** → `database/schema.sql`: the 3NF tables, PKs, FKs
   and CHECK constraints straight from the Group 5 case study; seed totals
   (PHP 88,000 awarded = PHP 88,000 disbursed) match the case document.
