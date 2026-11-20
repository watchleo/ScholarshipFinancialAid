# Unit II · Rudimentary Python programming

The Python API and its demo client use the following course topics. The project README covers all six Unit III topics and includes commands for running the two servers. [Project README](README.md)

| Course topic | Example to show |
| --- | --- |
| Python and IDLE | Run `python app.py` or open `app.py` in IDLE and press F5. |
| Basic syntax, variables, operators and data types | The rows in `database/seed_data.py` contain strings, numbers and null values. `services/report_service.py` calculates award balances. |
| Relational, equality and logical operators | `services/eligibility_service.py` compares GPA and household income with scholarship limits and combines the results with `and`. `demo.py` checks HTTP status codes with `==`. |
| Conditionals and loops | `review_application()` in `services/application_service.py` handles approval and rejection. `next_sequential_id()` in `utils/formatters.py` loops over existing IDs. |
| Built-in data structures | `database/seed_data.py` stores lists of tuples. `services/base_service.py` uses a dictionary to look up table definitions. `utils/formatters.py` uses a set to check whether an ID exists. |
| String manipulation | `utils/validators.py` trims strings and checks email formats. `utils/formatters.py` formats amounts and pads sequential IDs. |
| Functions | `api_request()` in `demo.py` accepts a method, path and optional payload and returns the HTTP status and decoded JSON. |
| Modules | `demo.py` imports `urllib.request` to send HTTP requests and `json` to encode and decode their bodies. |
| Packages | The routes in `api/` call functions from `services/`, which use `database/` and `utils/`. |
| Exceptions | `utils/exceptions.py` defines validation and conflict errors. `get_db()` in `database/db.py` rolls back on failure and closes connections in a `finally` block. |
| File management | `config.py` reads JSON settings. `utils/exporters.py` writes CSV and JSON reports and lists the saved files. |

For a classroom walkthrough, start the Python server and run `python demo.py` in another terminal. Steps 4 and 8 show validation and approval errors. Step 14 creates a CSV in `data/exports/`.
