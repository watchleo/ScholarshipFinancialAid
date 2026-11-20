"""End-to-end demo client - exercises the REST API (GET / POST / PUT / DELETE).

Uses ONLY the Python standard library (urllib), so there is nothing extra
to install. Start the server first in another terminal:

    python app.py

then run this demo:

    python demo.py

The client uses the classroom key by default. If you set SCHOLARSHIP_API_KEY
for the server, set the same value in the client terminal. The demo creates
sample records, writes a CSV report and removes its records at the end.
"""

import json
import os
import urllib.error
import urllib.request

BASE_URL = os.environ.get("FASTAPI_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
API_KEY = os.environ.get("SCHOLARSHIP_API_KEY", "school-demo-key")


# ---------------------------------------------------------------------------
# Tiny HTTP helper
# ---------------------------------------------------------------------------
def api_request(method, path, payload=None, *, expected_error=None):
    """Perform one HTTP request; returns (status_code, parsed_json_body).

    [Unit II] Exceptions: try / except / else-style handling with a clean
    message when the server is not reachable.
    """
    url = BASE_URL + path
    body = None
    headers = {"Accept": "application/json", "X-API-Key": API_KEY}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=body, headers=headers,
                                     method=method)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:  # context manager
            status = response.status
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:        # API answered with an error
        status = error.code
        raw = error.read().decode("utf-8")
    except urllib.error.URLError as error:         # server not reachable
        raise SystemExit(
            f"\nCannot reach {BASE_URL}\n"
            f"Reason: {error.reason}\n"
            "Start the server first:  python app.py") from error

    parsed = json.loads(raw) if raw else {}
    if status == 401:
        raise SystemExit("Authentication failed. Set SCHOLARSHIP_API_KEY to the server's key.")
    if status >= 400 and status != expected_error:
        message = parsed.get("error", {}).get("message", raw)
        raise SystemExit(f"{method} {path} returned HTTP {status}: {message}")
    if expected_error is not None and status != expected_error:
        raise SystemExit(f"{method} {path} returned HTTP {status}, expected {expected_error}.")
    return status, parsed


def money(amount):
    """25000 -> 'PHP 25,000.00'."""
    return f"PHP {amount:,.2f}" if amount is not None else "PHP 0.00"


def step(number, title):
    print("\n" + "=" * 72)
    print(f"STEP {number:>2}: {title}")
    print("=" * 72)


def line(label, value):
    print(f"   {label:<34}{value}")


# ---------------------------------------------------------------------------
# The demo itself
# ---------------------------------------------------------------------------
def run_demo():
    print("=" * 72)
    print(" SCHOLARSHIP & FINANCIAL AID MANAGEMENT SYSTEM - API DEMO")
    print(" (GET / POST / PUT / DELETE against a live FastAPI + SQLite server)")
    print("=" * 72)

    # 1 -- Health check (GET)
    step(1, "Health check  [GET /api/health]")
    status, body = api_request("GET", "/api/health")
    line("HTTP status", status)
    line("status", body["status"])
    line("total records", body["total_records"])
    line("applications seeded", body["tables"]["Applications"])
    line("disbursements seeded", body["tables"]["Disbursements"])

    # 2 -- List students (GET)
    step(2, "List students  [GET /api/students]")
    status, body = api_request("GET", "/api/students")
    line("HTTP status", status)
    line("count", body["count"])
    for student in body["data"]:
        print(f"   - {student['Student_ID']}  {student['Student_Name']:<18}"
              f"{student['Program']:<28} GPA {student['GPA']:.2f}  "
              f"Income {money(student['Household_Income'])}")

    # 3 -- Create a student (POST)
    step(3, "Register a new student  [POST /api/students]")
    status, body = api_request("POST", "/api/students", {
        "Student_Name": "Pedro Penduko",
        "Program": "BS Information Technology",
        "Year_Level": "1st Year",
        "Email": "pedro.penduko@student.edu.ph",
        "Contact_No": "0926-123-4567",
        "Household_Income": 14000,
        "GPA": 1.50,
    })
    line("HTTP status", status)
    line("message", body["message"])
    line("generated ID", body["data"]["Student_ID"])
    new_student_id = body["data"]["Student_ID"]

    # 4 -- Validation error demo (POST with a bad email -> HTTP 422)
    step(4, "Validation demo: invalid email  [POST /api/students]")
    status, body = api_request("POST", "/api/students", {
        "Student_Name": "Bad Email Test",
        "Program": "BS Nursing",
        "Year_Level": "1st Year",
        "Email": "not-an-email",
        "Contact_No": "0917-000-0000",
        "Household_Income": 10000,
        "GPA": 1.75,
    }, expected_error=422)
    line("HTTP status", status)
    line("error code", body["error"]["code"])
    line("Email problem", body["error"]["details"]["fields"]["Email"])

    # 5 -- Scholarships + eligibility screening (GET)
    step(5, "Scholarships + eligibility screening  [GET /api/scholarships]")
    status, body = api_request("GET", "/api/scholarships")
    line("HTTP status", status)
    for sc in body["data"]:
        print(f"   - {sc['Scholarship_ID']}  {sc['Scholarship_Name']:<32}"
              f"{sc['Scholarship_Type']:<12} slots {sc['Scholarship_Slots']}")

    status, body = api_request(
        "GET", f"/api/scholarships/SCH02/screening?student_id={new_student_id}")
    line("screening Pedro vs SCH02", body["data"]["note"])
    status, body = api_request("GET",
                               "/api/scholarships/SCH02/screening?student_id=S003")
    line("screening Jose (S003)", body["data"]["note"])

    # 6 -- Submit an application (POST)
    step(6, "Submit application  [POST /api/applications]")
    status, body = api_request("POST", "/api/applications", {
        "Student_ID": new_student_id,
        "Scholarship_ID": "SCH02",
        "Aid_ID": "FA02",
        "Term_ID": "T02",
        "Evaluator_ID": "E02",
    })
    line("HTTP status", status)
    line("message", body["message"])
    line("status", body["data"]["Status"])
    new_app_id = body["data"]["Application_ID"]

    # 7 -- Build the requirement checklist (POST x2)
    step(7, "Attach requirements  [POST /api/applications/<id>/requirements]")
    for requirement_id in ("R01", "R02"):
        status, body = api_request(
            "POST", f"/api/applications/{new_app_id}/requirements",
            {"Requirement_ID": requirement_id,
             "Requirement_Status": "Submitted",
             "Submitted_Date": "2025-11-20"})
        line(f"attach {requirement_id}", body["message"])
    line("all verified?", body["data"]["all_verified"])

    # 8 -- Try to approve while requirements are only 'Submitted' (422)
    step(8, "Approval blocked: requirements not Verified  [POST .../review]")
    status, body = api_request("POST",
                               f"/api/applications/{new_app_id}/review",
                               {"action": "approve", "award_amount": 10000},
                               expected_error=422)
    line("HTTP status", status)
    line("error code", body["error"]["code"])
    line("message", body["error"]["message"])

    # 9 -- Verify the requirements, then approve (POST)
    step(9, "Verify requirements, then approve")
    for requirement_id in ("R01", "R02", "R03", "R04"):
        api_request("POST", f"/api/applications/{new_app_id}/requirements",
                    {"Requirement_ID": requirement_id,
                     "Requirement_Status": "Verified",
                     "Submitted_Date": "2025-11-21"})
    status, body = api_request("GET",
                               f"/api/applications/{new_app_id}/requirements")
    line("checklist count", body["count"])
    line("all verified?", body["all_verified"])

    status, body = api_request("POST",
                               f"/api/applications/{new_app_id}/review",
                               {"action": "approve", "award_amount": 10000})
    line("HTTP status", status)
    line("message", body["message"])

    # 10 -- Disbursements (POST): first installment, then an overshoot warning
    step(10, "Disburse funds  [POST /api/applications/<id>/disbursements]")
    status, body = api_request(
        "POST", f"/api/applications/{new_app_id}/disbursements",
        {"Disbursement_Date": "2025-12-20", "Disbursement_Amount": 5000,
         "Payment_Method": "GCash", "Payment_Reference_No": "GC-DEMO-001",
         "Disbursement_Note": "1st installment"})
    line("HTTP status", status)
    line("message", body["message"])
    totals = body["application_totals"]
    line("remaining balance", money(totals["remaining"]))

    status, body = api_request(
        "POST", f"/api/applications/{new_app_id}/disbursements",
        {"Disbursement_Date": "2026-02-20", "Disbursement_Amount": 6000,
         "Payment_Method": "Bank Transfer",
         "Payment_Reference_No": "REF-DEMO-002",
         "Disbursement_Note": "2nd installment"})
    line("second disbursement", f"HTTP {status} - "
          f"{body['data']['Disbursement_ID']}")
    if "warning" in body:
        line("WARNING", body["warning"])
    second_disbursement_id = body["data"]["Disbursement_ID"]

    # 11 -- Application detail with joins + totals (GET)
    step(11, "Application detail  [GET /api/applications/<id>]")
    status, body = api_request("GET", f"/api/applications/{new_app_id}")
    detail = body["data"]
    line("HTTP status", status)
    line("student", f"{detail['Student']['Student_ID']} "
          f"{detail['Student']['Student_Name']}")
    line("scholarship", detail["Scholarship"]["Scholarship_Name"])
    line("aid", f"{detail['Financial_Aid']['Aid_Type']} funded by "
          f"{detail['Financial_Aid']['Sponsor_Name']}")
    line("term", f"{detail['Term']['Term_Name']} "
          f"{detail['Term']['Academic_Year']}")
    line("status / award", f"{detail['Status']} / {money(detail['Award_Amount'])}")
    line("disbursed so far", money(detail["Disbursement_Summary"]["total_amount"]))
    line("screening", detail["Screening"]["note"])

    # 12 -- Renewal for the next term (POST)
    step(12, "Renew for next term  [POST /api/applications/<id>/renew]")
    status, body = api_request("POST",
                               f"/api/applications/{new_app_id}/renew",
                               {"Term_ID": "T03"})
    line("HTTP status", status)
    line("message", body["message"])
    renewal_id = body["data"]["Application_ID"]
    line("renewal links back to", body["data"]["Previous_Application_ID"])

    # 13 -- Reports (GET)
    step(13, "Reports  [GET /api/reports/*]")
    status, body = api_request("GET", "/api/reports/summary")
    line("summary HTTP status", status)
    line("approved / pending / rejected",
         f"{body['approved']} / {body['pending']} / {body['rejected']}")
    line("total awarded", body["total_awarded_formatted"])
    line("total disbursed", body["total_disbursed_formatted"])

    status, body = api_request("GET", "/api/reports/sponsors")
    line("sponsors HTTP status", status)
    for sponsor in body["data"]:
        print(f"   - {sponsor['Sponsor_ID']}  {sponsor['Sponsor_Name']:<32}"
              f"budget {sponsor['budget_formatted']:>16}  committed "
              f"{sponsor['committed_formatted']:>15} "
              f"({sponsor['budget_utilization_pct']}%)")

    status, body = api_request("GET", "/api/reports/scholarships")
    line("scholarships HTTP status", status)
    for sc in body["data"]:
        print(f"   - {sc['Scholarship_ID']}  {sc['Scholarship_Name']:<32}"
              f"slots {sc['approved_applications']}/{sc['slots']} used "
              f"({sc['slot_utilization_pct']}%)")

    # 14 -- File export (POST) + listing exports (GET)
    step(14, "Export to CSV file  [POST /api/export]")
    status, body = api_request("POST", "/api/export",
                               {"entity": "applications", "format": "csv"})
    line("HTTP status", status)
    line("file", body["file"])
    line("rows written", body["rows"])
    line("size", f"{body['size_bytes']} bytes")

    status, body = api_request("GET", "/api/exports")
    line("exports on disk", body["count"])

    # 15 -- Update a student (PUT)
    step(15, "Update student contact number  [PUT /api/students/<id>]")
    status, body = api_request("PUT", f"/api/students/{new_student_id}",
                               {"Contact_No": "0926-999-8888"})
    line("HTTP status", status)
    line("message", body["message"])
    line("new contact no", body["data"]["Contact_No"])

    # 16 -- Referential integrity demo (DELETE blocked -> HTTP 409)
    step(16, "FK integrity: student with applications cannot be deleted")
    status, body = api_request("DELETE", f"/api/students/{new_student_id}",
                               expected_error=409)
    line("HTTP status", status)
    line("error code", body["error"]["code"])
    line("message", body["error"]["message"])

    # 17 -- Cleanup: remove the demo records (DELETE)
    step(17, "Cleanup: delete demo records  [DELETE ...]")
    status, body = api_request("DELETE",
                               f"/api/disbursements/{second_disbursement_id}")
    line(f"delete {second_disbursement_id}", body["message"])
    # Remove the renewal before the application that it references.
    status, body = api_request("DELETE", f"/api/applications/{renewal_id}")
    line(f"delete {renewal_id}", body["message"])
    status, body = api_request("DELETE",
                               f"/api/applications/{new_app_id}")
    line(f"delete {new_app_id}", body["message"])
    status, body = api_request("DELETE", f"/api/students/{new_student_id}")
    line(f"delete {new_student_id}", body["message"])

    # 18 -- Final state check (GET)
    step(18, "Final state  [GET /api/reports/summary]")
    status, body = api_request("GET", "/api/reports/summary")
    line("HTTP status", status)
    line("applications", body["records"]["Applications"])
    line("total awarded", body["total_awarded_formatted"])
    line("total disbursed", body["total_disbursed_formatted"])
    print("\nDemo complete. The demo records have been removed.")
    print("The CSV report from step 14 is in data/exports/.")


if __name__ == "__main__":
    run_demo()
