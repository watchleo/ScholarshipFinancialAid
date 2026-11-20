# Scholarship and Financial Aid Management System — REST API

A Python web application (Flask + SQLite) built on the **Group 5 case study**,
*"Scholarship and Financial Aid Management System"*. The database implements
the normalized **3NF** schema from the case analysis (PKs, FKs, and all sample
rows included), and exposes it through a REST API.

The project includes an Ionic React dashboard at `/` for viewing summary data,
students, scholarships, and applications. The Flask REST API remains available
under `/api` for clients and integrations.

---

## What the app demonstrates

### Unit III — Data Exchange using API (the 3 chosen topics)
| # | Topic | Where |
|---|-------|-------|
| 1 | **HTTP API Server** | `app.py` starts a Flask HTTP server; `api/` package defines all routes |
| 2 | **HTTP GET and POST requests** | GET for reads, POST for creating/approve/disburse/renew/export — plus PUT and DELETE for full CRUD |
| 3 | **REST API** | Resource URLs (`/api/students`, `/api/applications/A001`), JSON in/out, proper status codes (200 / 201 / 400 / 404 / 409 / 422) |

### Unit II — Rudimentary Python Programming (ALL topics except Virtual Environment)
Every topic is used in the real code — see **`UNIT_II_CONCEPT_MAP.md`** for a
topic-by-topic map with exact file locations (great for the defense).

> **Note on Virtual Environment:** per the TO-DO, no venv is required.
> The backend's only external dependency is Flask; everything else is the Python
> standard library (`sqlite3`, `json`, `csv`, `re`, `logging`, `argparse`,
> `datetime`, `unittest`, `urllib`).

---

## Tech stack

- **Python 3.10+** (written and tested on 3.12)
- **Flask 3** — Python API and production web server
- **Ionic React** — browser dashboard, built with Vite
- **SQLite** — built into Python, stored in `database/scholarship.db`
- **Node.js 20+** — frontend dependency installation and build

## Project structure

```
scholarship-financial-aid-api/
├── app.py                  # entry point — starts the HTTP API server
├── demo.py                 # end-to-end demo client (stdlib only)
├── config.py               # loads settings from config.json
├── config.json             # host, port, paths (no code, just settings)
├── requirements.txt        # Flask
├── frontend/               # Ionic React application (Vite)
│   ├── package.json
│   └── src/
│       ├── App.jsx          # dashboard pages and API data
│       └── theme.css        # Ionic dashboard theme
│
├── database/               # PACKAGE: schema + connection + seed data
│   ├── schema.sql          #   3NF tables with PKs, FKs, CHECK constraints
│   ├── seed_data.py        #   exact case-study sample rows
│   └── db.py               #   connections, init, reset, seeding
│
├── services/               # PACKAGE: business logic
│   ├── base_service.py     #   generic CRUD + table registry + auto IDs
│   ├── catalog_service.py  #   terms / evaluators / requirements / sponsors / aids
│   ├── student_service.py  #   student CRUD + per-student applications
│   ├── application_service.py  # lifecycle: submit → checklist → review → renew
│   ├── disbursement_service.py # installment tracking + overshoot warning
│   ├── eligibility_service.py  # GPA / income screening (stored, not enforced)
│   └── report_service.py   #   reports + CSV/JSON exports
│
├── api/                    # PACKAGE: HTTP layer (Flask blueprints)
│   ├── __init__.py         #   app factory, error handlers, request logging
│   ├── common.py           #   JSON body parsing helper
│   ├── students.py         #   /api/students
│   ├── scholarships.py     #   /api/scholarships (+ screening)
│   ├── catalog.py          #   /api/terms, /evaluators, /requirements, /sponsors, /financial-aids
│   ├── applications.py     #   /api/applications (+ nested resources)
│   ├── reports.py          #   /api/reports/* and /api/export
│   └── static/              # generated frontend build (not committed)
│
├── utils/                  # PACKAGE: shared helpers
│   ├── exceptions.py       #   custom exception hierarchy
│   ├── validators.py       #   field validation for every payload
│   ├── formatters.py       #   money formatting + auto ID generation
│   ├── exporters.py        #   CSV / JSON file export
│   └── app_logger.py       #   console + file logging
│
├── tests/
│   └── test_api.py         # 21 automated tests (unittest)
│
├── logs/app.log            # created at runtime (audit trail)
└── data/exports/           # created at runtime (exported files)
```

---

## Quick start (no virtual environment)

```bash
# 1. install the Python backend dependency
pip install -r requirements.txt

# 2. install and build the Ionic React dashboard (Node.js 20+)
cd frontend
npm ci
npm run build
cd ..

# 3. start the server (creates + seeds the database on first run)
python app.py

# 4. open the dashboard or API health check in a browser
#    http://127.0.0.1:5000/              -> dashboard
#    http://127.0.0.1:5000/api/health    -> status + row counts
```

For frontend development with hot reload, run `npm run dev` from `frontend/`
while the Flask API is running. Vite proxies `/api` requests to Flask.

Useful flags:

```bash
python app.py --port 5001     # different port
python app.py --reset-db      # wipe, recreate and reseed the database
python app.py --init-only     # just prepare the database, then exit
```

The project also runs in **IDLE**: open `app.py` and press **F5**.

## Run the demo

With the server running (step 2 above), open a **second** terminal:

```bash
python demo.py
```

The demo walks through the whole workflow in 18 steps: health check, list
students, register a student (with a deliberate validation error), eligibility
screening, submit application, build the requirement checklist, a blocked
approval, verification, approval, two disbursements (including the overshoot
warning), renewal, reports, CSV export, update, a blocked delete (foreign key
integrity), and cleanup. It leaves the database exactly as it found it.

## Run the tests

```bash
python -m unittest discover -s tests -v
```

21 tests run against a throwaway database — the real one is never touched.

---

## API reference

Base URL: `http://127.0.0.1:5000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | status + row counts per table |
| GET | `/api/students` | list students (`?search=&program=&year_level=`) |
| POST | `/api/students` | register a student |
| GET | `/api/students/<id>` | one student |
| PUT | `/api/students/<id>` | partial update |
| DELETE | `/api/students/<id>` | delete (409 if applications exist) |
| GET | `/api/students/<id>/applications` | the student's applications + summary |
| GET | `/api/scholarships` | list scholarships (`?type=`) |
| POST/PUT/DELETE | `/api/scholarships[/<id>]` | manage scholarships |
| GET | `/api/scholarships/<id>/screening?student_id=S001` | eligibility screening |
| GET/POST/PUT/DELETE | `/api/terms[/<id>]` | manage academic terms |
| GET/POST/PUT/DELETE | `/api/evaluators[/<id>]` | manage evaluators |
| GET/POST/PUT/DELETE | `/api/requirements[/<id>]` | manage requirement types |
| GET/POST/PUT/DELETE | `/api/sponsors[/<id>]` | manage sponsors |
| GET/POST/PUT/DELETE | `/api/financial-aids[/<id>]` | manage aid types (`?sponsor_id=`) |
| GET | `/api/applications` | list (`?status=&student_id=&term_id=&scholarship_id=none&evaluator_id=&aid_id=`) |
| POST | `/api/applications` | submit (always starts `Pending`) |
| GET | `/api/applications/<id>` | full detail: joins, checklist, totals, screening |
| PUT | `/api/applications/<id>` | partial update (status/award protected) |
| DELETE | `/api/applications/<id>` | delete (checklist + disbursements cascade) |
| GET/POST | `/api/applications/<id>/requirements` | checklist |
| DELETE | `/api/applications/<id>/requirements/<req_id>` | remove one checklist entry |
| POST | `/api/applications/<id>/review` | approve / reject |
| POST | `/api/applications/<id>/renew` | create renewal for another term |
| GET | `/api/applications/<id>/screening` | eligibility report |
| GET/POST | `/api/applications/<id>/disbursements` | installments |
| GET | `/api/disbursements` | all disbursements (`?application_id=&payment_method=`) |
| GET/DELETE | `/api/disbursements/<id>` | one disbursement |
| GET | `/api/reports/summary` | counts + totals |
| GET | `/api/reports/applications` | per-term aggregation (`?term_id=`) |
| GET | `/api/reports/disbursements` | award vs disbursed + warnings |
| GET | `/api/reports/sponsors` | budget vs committed |
| GET | `/api/reports/scholarships` | slot utilization |
| POST | `/api/export` | `{"entity": "applications", "format": "csv"\|"json"}` |
| GET | `/api/exports` | list exported files |

### Sample requests (curl)

```bash
# health check
curl http://127.0.0.1:5000/api/health

# one application with all joins
curl http://127.0.0.1:5000/api/applications/A001

# register a student (ID auto-generated -> S006)
curl -X POST http://127.0.0.1:5000/api/students \
  -H "Content-Type: application/json" \
  -d "{\"Student_Name\": \"Pedro Penduko\", \"Program\": \"BS Information Technology\", \"Year_Level\": \"1st Year\", \"Email\": \"pedro.penduko@student.edu.ph\", \"Contact_No\": \"0926-123-4567\", \"Household_Income\": 14000, \"GPA\": 1.5}"

# approve an application
curl -X POST http://127.0.0.1:5000/api/applications/A007/review \
  -H "Content-Type: application/json" \
  -d "{\"action\": \"approve\", \"award_amount\": 10000}"

# summary report
curl http://127.0.0.1:5000/api/reports/summary
```

> Windows PowerShell tip: use `curl.exe` instead of `curl`, or test with
> Postman / the browser (GET endpoints) — or just run `python demo.py`.

### Example: application detail (truncated)

```json
{
  "data": {
    "Application_ID": "A001",
    "Application_Date": "2025-06-10",
    "Status": "Approved",
    "Award_Amount": 25000.0,
    "Previous_Application_ID": null,
    "Student": {"Student_ID": "S001", "Student_Name": "Juan Dela Cruz", "...": "..."},
    "Scholarship": {"Scholarship_ID": "SCH01", "...": "..."},
    "Financial_Aid": {"Aid_ID": "FA01", "Sponsor_Name": "University Financial Aid Office", "...": "..."},
    "Term": {"Term_ID": "T01", "Term_Name": "1st Semester", "Academic_Year": "2025-2026"},
    "Requirement_Summary": {"total": 4, "Verified": 4, "all_verified": true},
    "Disbursement_Summary": {"count": 2, "total_amount": 25000.0},
    "Balance": {"award_amount": 25000.0, "disbursed": 25000.0, "remaining": 0.0},
    "Screening": {"eligible": true, "checks": ["..."], "note": "Student meets both scholarship limits."}
  }
}
```

### Error format (always JSON)

```json
{
  "error": {
    "code": "validation_failed",
    "message": "Some fields failed validation.",
    "details": {"fields": {"Email": "must be a valid email address (e.g. juan@university.edu.ph)."}}
  }
}
```

| Status | Meaning |
|--------|---------|
| 200 / 201 | success / created |
| 400 | request body is not valid JSON |
| 404 | record or route not found |
| 409 | conflict (duplicate ID, blocked delete, illegal status transition) |
| 422 | validation or business-rule violation (field details included) |
| 500 | unexpected error (full traceback in `logs/app.log`) |

---

## Business rules implemented

- New applications always start **Pending**; `Status` and `Award_Amount` can
  only change through the **review** endpoint.
- **Approval** requires: application is Pending + every attached requirement
  is **Verified** + a positive award amount. Rejection sets the award to 0.
- Only **Approved** applications accept disbursements.
- **Renewals** link to the previous application (`Previous_Application_ID`),
  must target a different term, and only Approved applications can renew.
- Deleting a student/sponsor/etc. that is still referenced fails with a clear
  409 (foreign-key integrity). Deleting an application cascades to its
  checklist entries and disbursements.

## Case-study limitations honored (by design)

- Eligibility rules (GPA / income limits, slots, budget) are **stored but not
  automatically enforced** — the screening endpoints *report* eligibility, and
  approving an ineligible application returns a `screening_warning`.
- Disbursements are **not hard-validated** against `Award_Amount` — exceeding
  it is allowed but flagged with a `warning` in the response.
- One evaluator per application; only current status is kept (no history
  beyond the log file), matching the documented scope.

## Data sources

All seed rows come from the Group 5 case analysis (3NF tables), including the
"(Extra Sample)" rows SP04 (Rizal Alumni Association) and SCH03 (Alumni Legacy
Scholarship). Totals after seeding: **PHP 88,000 awarded = PHP 88,000
disbursed**, zero balance — matching the case-study data.

## Possible extensions (not chosen in the TO-DO)

- **API Authentication** (Unit III topic 6): add an `X-API-Key` header check
  in a Flask `before_request` hook with keys stored in a JSON file.
- **PHP Web API** (Unit III topic 5): the same SQLite file could be consumed
  by a small PHP endpoint if ever required.
