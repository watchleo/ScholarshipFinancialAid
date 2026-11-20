"""Exercise the FastAPI routes against a temporary SQLite database.

Run from the application directory with python -m unittest discover -s tests -v.
"""

import os
import tempfile
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import create_app
from config import SETTINGS

TEST_KEY = "integration-test-key"

STUDENT_PAYLOAD = {
    "Student_Name": "Test Student",
    "Program": "BS Information Technology",
    "Year_Level": "1st Year",
    "Email": "test.student@student.edu.ph",
    "Contact_No": "0999-888-7777",
    "Household_Income": 13000,
    "GPA": 1.25,
}


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        directory = stack.enter_context(tempfile.TemporaryDirectory())
        self.db_path = os.path.join(directory, "scholarship.db")
        stack.enter_context(patch.dict(os.environ, {"SCHOLARSHIP_API_KEY": TEST_KEY}))
        stack.enter_context(patch.dict(SETTINGS, {"exports_dir": os.path.join(directory, "exports")}))
        self.app = create_app(db_path=self.db_path)
        self.client = stack.enter_context(
            TestClient(self.app, headers={"X-API-Key": TEST_KEY})
        )

    # -- small helpers ------------------------------------------------------
    def get(self, path):
        return self.client.get(path)

    def post(self, path, payload):
        return self.client.post(path, json=payload)

    def put(self, path, payload):
        return self.client.put(path, json=payload)

    def delete(self, path):
        return self.client.delete(path)

    # -- health & seed data --------------------------------------------------
    def test_01_health_ok(self):
        response = self.get("/api/health")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["total_records"], 59)  # 5+3+3+3+5+4+4+6+19+7

    def test_02_seed_counts(self):
        self.assertEqual(len(self.get("/api/students").json()["data"]), 5)
        self.assertEqual(len(self.get("/api/scholarships").json()["data"]), 3)
        self.assertEqual(len(self.get("/api/sponsors").json()["data"]), 4)
        self.assertEqual(len(self.get("/api/applications").json()["data"]), 6)
        self.assertEqual(len(self.get("/api/disbursements").json()["data"]), 7)
        checklist = self.get("/api/applications/A006/requirements").json()
        self.assertEqual(checklist["count"], 3)

    # -- students CRUD --------------------------------------------------------
    def test_03_student_crud(self):
        created = self.post("/api/students", STUDENT_PAYLOAD)
        self.assertEqual(created.status_code, 201)
        student_id = created.json()["data"]["Student_ID"]
        self.assertEqual(student_id, "S006")  # auto-generated after S001..S005

        updated = self.put(f"/api/students/{student_id}",
                           {"Contact_No": "0999-111-2222"})
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["data"]["Contact_No"],
                         "0999-111-2222")

        deleted = self.delete(f"/api/students/{student_id}")
        self.assertEqual(deleted.status_code, 200)

    def test_04_student_validation_error(self):
        response = self.post("/api/students",
                             {**STUDENT_PAYLOAD, "Email": "nope"})
        self.assertEqual(response.status_code, 422)
        fields = response.json()["error"]["details"]["fields"]
        self.assertIn("Email", fields)

    def test_05_student_not_found(self):
        self.assertEqual(self.get("/api/students/S999").status_code, 404)

    # -- applications: detail & seeded lifecycle facts ------------------------
    def test_06_application_detail_joins_and_totals(self):
        response = self.get("/api/applications/A001")
        self.assertEqual(response.status_code, 200)
        detail = response.json()["data"]
        self.assertEqual(detail["Student"]["Student_Name"], "Juan Dela Cruz")
        self.assertEqual(detail["Scholarship"]["Scholarship_ID"], "SCH01")
        self.assertEqual(detail["Financial_Aid"]["Sponsor_ID"], "SP01")
        self.assertEqual(detail["Requirement_Summary"]["total"], 4)
        self.assertTrue(detail["Requirement_Summary"]["all_verified"])
        self.assertEqual(detail["Disbursement_Summary"]["total_amount"], 25000)
        self.assertEqual(detail["Balance"]["remaining"], 0)

    def test_07_renewal_link_in_seed(self):
        detail = self.get("/api/applications/A004").json()["data"]
        self.assertEqual(detail["Previous_Application_ID"], "A001")

    # -- full lifecycle on a fresh application --------------------------------
    def test_08_full_lifecycle(self):
        # create a student + application
        student = self.post("/api/students", STUDENT_PAYLOAD).json()["data"]
        created = self.post("/api/applications", {
            "Student_ID": student["Student_ID"],
            "Scholarship_ID": "SCH02", "Aid_ID": "FA02",
            "Term_ID": "T01", "Evaluator_ID": "E01",
        })
        self.assertEqual(created.status_code, 201)
        app_id = created.json()["data"]["Application_ID"]
        self.assertEqual(created.json()["data"]["Status"], "Pending")

        # cannot set status/award at submission
        bad = self.post("/api/applications", {
            "Student_ID": student["Student_ID"], "Aid_ID": "FA02",
            "Term_ID": "T01", "Evaluator_ID": "E01", "Status": "Approved",
        })
        self.assertEqual(bad.status_code, 422)

        # approval blocked while requirements are not Verified
        self.post(f"/api/applications/{app_id}/requirements",
                  {"Requirement_ID": "R01", "Requirement_Status": "Submitted",
                   "Submitted_Date": "2026-01-10"})
        blocked = self.post(f"/api/applications/{app_id}/review",
                            {"action": "approve", "award_amount": 5000})
        self.assertEqual(blocked.status_code, 422)

        # verify everything, then approve
        self.post(f"/api/applications/{app_id}/requirements",
                  {"Requirement_ID": "R01", "Requirement_Status": "Verified",
                   "Submitted_Date": "2026-01-11"})
        approved = self.post(f"/api/applications/{app_id}/review",
                             {"action": "approve", "award_amount": 5000})
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.json()["data"]["Status"], "Approved")

        # double review -> conflict
        again = self.post(f"/api/applications/{app_id}/review",
                          {"action": "approve", "award_amount": 5000})
        self.assertEqual(again.status_code, 409)

        # disbursement + overshoot warning
        first = self.post(f"/api/applications/{app_id}/disbursements",
                          {"Disbursement_Date": "2026-02-01",
                           "Disbursement_Amount": 3000,
                           "Payment_Method": "GCash",
                           "Payment_Reference_No": "GC-T-001"})
        self.assertEqual(first.status_code, 201)
        second = self.post(f"/api/applications/{app_id}/disbursements",
                           {"Disbursement_Date": "2026-03-01",
                            "Disbursement_Amount": 3000,
                            "Payment_Method": "GCash",
                            "Payment_Reference_No": "GC-T-002"})
        self.assertIn("warning", second.json())  # 6000 > 5000 award

        # cleanup (cascades the checklist + disbursements)
        deleted = self.delete(f"/api/applications/{app_id}")
        self.assertEqual(deleted.status_code, 200)
        self.delete(f"/api/students/{student['Student_ID']}")

    def test_09_renewal_workflow(self):
        renewed = self.post("/api/applications/A001/renew", {"Term_ID": "T03"})
        self.assertEqual(renewed.status_code, 201)
        body = renewed.json()
        new_id = body["data"]["Application_ID"]
        self.assertEqual(body["data"]["Previous_Application_ID"], "A001")
        self.assertEqual(body["data"]["Status"], "Pending")

        # same term -> conflict
        same = self.post("/api/applications/A001/renew", {"Term_ID": "T01"})
        self.assertEqual(same.status_code, 409)

        # cleanup
        self.delete(f"/api/applications/{new_id}")

    def test_10_renewal_requires_approved(self):
        response = self.post("/api/applications/A006/renew", {"Term_ID": "T01"})
        self.assertEqual(response.status_code, 422)  # A006 is Pending

    # -- foreign keys & integrity ---------------------------------------------
    def test_11_application_fk_validation(self):
        response = self.post("/api/applications", {
            "Student_ID": "S999", "Aid_ID": "FA02",
            "Term_ID": "T01", "Evaluator_ID": "E01",
        })
        self.assertEqual(response.status_code, 422)
        fields = response.json()["error"]["details"]["fields"]
        self.assertIn("Student_ID", fields)

    def test_12_delete_blocked_by_foreign_key(self):
        # S001 still has applications A001 + A004
        response = self.delete("/api/students/S001")
        self.assertEqual(response.status_code, 409)

        # sponsor SP01 funds FA01/FA03
        response = self.delete("/api/sponsors/SP01")
        self.assertEqual(response.status_code, 409)

    def test_13_delete_application_cascades(self):
        student = self.post("/api/students", STUDENT_PAYLOAD).json()["data"]
        app = self.post("/api/applications", {
            "Student_ID": student["Student_ID"], "Aid_ID": "FA02",
            "Term_ID": "T01", "Evaluator_ID": "E01",
        }).json()["data"]
        app_id = app["Application_ID"]
        self.post(f"/api/applications/{app_id}/requirements",
                  {"Requirement_ID": "R01", "Requirement_Status": "Verified",
                   "Submitted_Date": "2026-01-05"})

        deleted = self.delete(f"/api/applications/{app_id}")
        self.assertEqual(deleted.status_code, 200)
        message = deleted.json()["message"]
        self.assertIn("cascade", message.lower())

        checklist = self.get(f"/api/applications/{app_id}/requirements")
        self.assertEqual(checklist.status_code, 404)
        self.delete(f"/api/students/{student['Student_ID']}")

    # -- filters & reports -----------------------------------------------------
    def test_14_list_filters(self):
        approved = self.get("/api/applications?status=Approved")
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.json()["count"], 4)

        juan = self.get("/api/applications?student_id=s001")
        self.assertEqual(juan.json()["count"], 2)

        no_scholarship = self.get("/api/applications?scholarship_id=none")
        self.assertEqual(no_scholarship.json()["count"], 1)  # A003

        bad = self.get("/api/applications?status=Maybe")
        self.assertEqual(bad.status_code, 422)

    def test_15_reports_summary_totals(self):
        body = self.get("/api/reports/summary").json()
        self.assertEqual(body["approved"], 4)
        self.assertEqual(body["pending"], 1)
        self.assertEqual(body["rejected"], 1)
        self.assertEqual(body["total_awarded"], 88000)
        self.assertEqual(body["total_disbursed"], 88000)
        self.assertEqual(body["remaining_balance"], 0)

    def test_16_sponsor_report_values(self):
        data = self.get("/api/reports/sponsors").json()["data"]
        by_id = {s["Sponsor_ID"]: s for s in data}
        self.assertEqual(by_id["SP01"]["committed"], 50000)  # A001 + A004
        self.assertEqual(by_id["SP02"]["committed"], 8000)   # A002
        self.assertEqual(by_id["SP03"]["committed"], 30000)  # A005
        self.assertEqual(by_id["SP04"]["committed"], 0)

    def test_17_scholarship_report_values(self):
        data = self.get("/api/reports/scholarships").json()["data"]
        by_id = {s["Scholarship_ID"]: s for s in data}
        self.assertEqual(by_id["SCH01"]["approved_applications"], 2)
        self.assertEqual(by_id["SCH02"]["approved_applications"], 2)
        self.assertEqual(by_id["SCH02"]["pending_applications"], 1)  # A006
        self.assertEqual(by_id["SCH03"]["remaining_slots"], 20)

    def test_18_screening_endpoints(self):
        # Jose (S003): income 25,000 > SCH02 limit 15,000 -> not eligible
        body = self.get("/api/scholarships/SCH02/screening?student_id=S003")
        self.assertFalse(body.json()["data"]["eligible"])

        # Ana (S004): income 9,000 <= 15,000 and GPA 1.25 <= 2.50 -> eligible
        body = self.get("/api/scholarships/SCH02/screening?student_id=S004")
        self.assertTrue(body.json()["data"]["eligible"])

        # A003 has no scholarship -> eligible is None with an explanatory note
        body = self.get("/api/applications/A003/screening")
        self.assertIsNone(body.json()["data"]["eligible"])

    # -- exports ----------------------------------------------------------------
    def test_19_export_csv_and_listing(self):
        response = self.post("/api/export",
                             {"entity": "students", "format": "csv"})
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["rows"], 5)
        self.assertTrue(body["file"].endswith(".csv"))
        self.assertTrue(os.path.exists(body["path"]))  # really on disk

        listing = self.get("/api/exports").json()
        self.assertGreaterEqual(listing["count"], 1)

        bad = self.post("/api/export", {"entity": "dragons", "format": "csv"})
        self.assertEqual(bad.status_code, 422)

    # -- API robustness ----------------------------------------------------------
    def test_20_bad_json_body(self):
        response = self.client.post(
            "/api/students", content="this is not json",
            headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 400)

    def test_21_unknown_route_returns_json_404(self):
        response = self.get("/api/unicorns")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.json())

    def test_missing_and_invalid_keys_do_not_read_or_write(self):
        with TestClient(self.app) as visitor:
            for headers in ({}, {"X-API-Key": "school-demo-key"}):
                with self.subTest(headers=headers):
                    self.assertEqual(visitor.get("/api/students", headers=headers).status_code, 401)
                    response = visitor.post("/api/students", json=STUDENT_PAYLOAD, headers=headers)
                    self.assertEqual(response.status_code, 401)
        self.assertEqual(self.get("/api/students").json()["count"], 5)

    def test_created_student_survives_app_restart(self):
        response = self.post("/api/students", STUDENT_PAYLOAD)
        self.assertEqual(response.status_code, 201)
        created = response.json()["data"]

        restored_app = create_app(db_path=self.db_path)
        with TestClient(restored_app, headers={"X-API-Key": TEST_KEY}) as client:
            response = client.get(f"/api/students/{created['Student_ID']}")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["data"], created)

    def test_openapi_describes_authenticated_resources(self):
        with TestClient(self.app) as visitor:
            response = visitor.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        methods = schema["paths"]["/api/students"]
        for verb in ("get", "post"):
            schemes = schema["components"]["securitySchemes"]
            required = methods[verb]["security"]
            self.assertTrue(any(
                schemes[name].get("name") == "X-API-Key"
                for option in required for name in option
            ))


if __name__ == "__main__":
    unittest.main(verbosity=2)
