# Scholarship & Financial Aid project guide

The dashboard and the interactive API reference run on the FastAPI server. PHP provides a second HTTP entry point. PHP sends the caller’s API key to FastAPI, so both services use the same SQLite records and application rules.

## Start the services

In the directory containing `app.py`, install the Python dependencies and start FastAPI.

```sh
python -m pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** for the dashboard or **http://127.0.0.1:5000/docs** to browse and run endpoints. In a second terminal in the same folder, start the PHP 8 CLI server.

```sh
php -S 127.0.0.1:8080 php-api/index.php
```

The shared classroom key is `school-demo-key`. To use a different key, set `SCHOLARSHIP_API_KEY` before starting FastAPI and enter that value in your client. PHP reads `FASTAPI_BASE_URL` if FastAPI runs at a different address.

## Demonstrate all six topics

Run these examples in a third terminal with curl. The first request shows what happens when the API key is missing. The second reads the scholarship catalog with authentication.

```sh
curl -i http://127.0.0.1:5000/api/scholarships
curl -i -H "X-API-Key: school-demo-key" http://127.0.0.1:5000/api/scholarships
```

The responses should be **401 Unauthorized** and **200 OK**. Next, submit an application through the PHP Web API.

```sh
curl -i http://127.0.0.1:8080/api/applications \
  -H "X-API-Key: school-demo-key" \
  -H "Content-Type: application/json" \
  -d '{"Student_ID":"S003","Scholarship_ID":"SCH03","Aid_ID":"FA01","Term_ID":"T03","Evaluator_ID":"E01"}'
```

Look for **201 Created**, a new `data.Application_ID`, and a `Pending` status. Use the returned ID in the FastAPI GET request below. On a freshly seeded database the ID is `A007`. The PHP report will also include your new pending application.

```sh
curl -H "X-API-Key: school-demo-key" http://127.0.0.1:5000/api/applications/A007
curl -H "X-API-Key: school-demo-key" http://127.0.0.1:8080/api/application-status-counts
```

You can repeat the FastAPI requests in the browser. Open `/docs`, select **Authorize**, enter your key, and expand an endpoint. The list, create, detail, update, and delete operations demonstrate the REST resource model.

## Scholarship workflow

- **Submit** an application for a student, term, aid type, and evaluator. A scholarship is optional. Every new application starts as pending.
- **Screen** the student against the scholarship’s GPA and household income limits. The screening result informs the evaluator’s decision.
- **Review** a pending application using its requirement checklist. Approval needs verified requirements and a positive award.
- **Track payments** against approved awards. The detail response includes the disbursed total and remaining balance.
- **Renew** an approved application for a different term. The new application links back to the previous one.

## Verify the project

```sh
python -m unittest discover -s tests -v
```

The API tests use temporary SQLite databases. With the PHP CLI on your PATH, the suite also starts both servers and tests a PHP submission end to end. With FastAPI running, `python demo.py` walks through the seeded case study, exercises validation and review rules, and writes an example CSV export.

The route handlers live in `api/`, the scholarship rules in `services/`, and the schema and sample records in `database/`. The browser interface lives in `frontend/` and the PHP service in `php-api/`. For the project's Python programming examples, see the [Unit II concept map](UNIT_II_CONCEPT_MAP.md).
