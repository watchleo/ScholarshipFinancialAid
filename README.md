# Scholarship & Financial Aid

A classroom app for tracking scholarship applications, eligibility, awards, and payments. FastAPI and PHP expose the same scholarship records over HTTP. The dashboard uses plain HTML, CSS, JavaScript, and the system font.

## Run locally

With Python 3.10+ installed, run these commands from the repository root.

```sh
cd scholarship-financial-aid-api
python -m pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** for the dashboard. The first run creates a SQLite database with the Group 5 case-study records. Open **http://127.0.0.1:5000/docs** for the interactive API reference and enter `school-demo-key` under **Authorize**.

For the PHP part of the assignment, install the PHP 8 CLI and open a second terminal in the same project folder.

```sh
php -S 127.0.0.1:8080 php-api/index.php
```

## Unit III topics

| Topic | What to show in class |
| --- | --- |
| 1. HTTP API server | Start Uvicorn with `python app.py` and request `/api/health`. |
| 2. HTTP GET and POST requests | List scholarships with GET, submit an application with POST, then retrieve its assigned ID. |
| 3. FastAPI | Use **Try it out** at `/docs` to call a Python route. The OpenAPI schema is at `/openapi.json`. |
| 4. REST API | Each application has a URL such as `/api/applications/A001`. A successful POST returns 201 and a missing record returns 404. |
| 5. PHP Web API | Call the PHP server on port 8080 to submit an application or get counts by application status. |
| 6. API authentication | Call a protected endpoint without a key to see 401. Send the same request with the `X-API-Key` header to read the data. |

The project guide includes copyable requests for a cross-service demo, the automated test command, and the application review rules. [Open the project guide](scholarship-financial-aid-api/README.md)

A copy of the project folder is also available as a [downloadable ZIP](scholarship-financial-aid-api.zip).
