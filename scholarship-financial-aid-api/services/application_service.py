"""Application lifecycle: the heart of the system.

Implements the case-study workflow:
    submission -> requirement checklist -> evaluator review -> approval /
    rejection -> disbursements (see disbursement_service) -> renewal.

Business rules enforced here:
  * a new application always starts as Pending;
  * Status / Award_Amount can only change through the review endpoint;
  * approval requires every attached requirement to be Verified;
  * only Pending applications can be reviewed (409 otherwise);
  * renewals link back to the previous application and must target a
    different academic term for the same student.
"""

from datetime import date

from database import db
from services import base_service, eligibility_service
from utils import validators
from utils.app_logger import get_logger
from utils.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from utils.formatters import format_money

logger = get_logger("applications")

# query parameter -> physical column (whitelisted list filters)
LIST_FILTERS = {
    "status": "a.Status",
    "student_id": "a.Student_ID",
    "aid_id": "a.Aid_ID",
    "term_id": "a.Term_ID",
    "evaluator_id": "a.Evaluator_ID",
    "previous_application_id": "a.Previous_Application_ID",
}

# The SELECT used by the list endpoint (names joined in for readability)
_LIST_SQL = """
SELECT a.Application_ID, a.Application_Date, a.Status, a.Award_Amount,
       a.Previous_Application_ID,
       a.Student_ID, s.Student_Name,
       a.Scholarship_ID, sc.Scholarship_Name,
       a.Aid_ID, fa.Aid_Type,
       a.Term_ID, t.Term_Name, t.Academic_Year,
       a.Evaluator_ID, e.Evaluator_Name
FROM Applications a
JOIN Students s        ON s.Student_ID = a.Student_ID
LEFT JOIN Scholarship sc ON sc.Scholarship_ID = a.Scholarship_ID
JOIN Financial_Aid fa  ON fa.Aid_ID = a.Aid_ID
JOIN Academic_Terms t  ON t.Term_ID = a.Term_ID
JOIN Evaluators e      ON e.Evaluator_ID = a.Evaluator_ID
"""


def list_applications(**filters):
    """List applications with optional filters (all whitelisted above)."""
    conditions, params = [], []
    applied = {}

    for param, column in LIST_FILTERS.items():
        value = filters.get(param)
        if not value:
            continue
        value = str(value).strip()
        if param == "status":
            if value not in validators.APPLICATION_STATUSES:
                raise ValidationError(
                    "Invalid status filter.",
                    details={"fields": {
                        "status": "must be one of: "
                        + ", ".join(validators.APPLICATION_STATUSES)}})
            applied[param] = value
            conditions.append(f"{column} = ?")
            params.append(value)
        elif param.endswith("_id"):
            upper = value.upper()
            applied[param] = upper
            conditions.append(f"{column} = ?")
            params.append(upper)

    # special filter: scholarship_id=none -> applications without a scholarship
    scholarship_value = str(filters.get("scholarship_id") or "").strip()
    if scholarship_value.lower() == "none":
        applied["scholarship_id"] = "none"
        conditions.append("a.Scholarship_ID IS NULL")
    elif scholarship_value:
        applied["scholarship_id"] = scholarship_value.upper()
        conditions.append("a.Scholarship_ID = ?")
        params.append(scholarship_value.upper())

    sql = _LIST_SQL
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY a.Application_Date, a.Application_ID"

    with db.get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    data = [dict(row) for row in rows]
    return {"count": len(data), "filters": applied, "data": data}


# ---------------------------------------------------------------------------
# Detail (single application with everything joined in)
# ---------------------------------------------------------------------------
_DETAIL_SQL = """
SELECT a.Application_ID, a.Application_Date, a.Status, a.Award_Amount,
       a.Previous_Application_ID,
       s.Student_ID, s.Student_Name, s.Program, s.Year_Level, s.Email,
       s.Contact_No, s.Household_Income, s.GPA,
       sc.Scholarship_ID AS Sch_ID, sc.Scholarship_Name, sc.Scholarship_Type,
       fa.Aid_ID, fa.Aid_Type, fa.Aid_Description,
       sp.Sponsor_ID, sp.Sponsor_Name,
       t.Term_ID, t.Term_Name, t.Academic_Year,
       e.Evaluator_ID, e.Evaluator_Name
FROM Applications a
JOIN Students s         ON s.Student_ID = a.Student_ID
LEFT JOIN Scholarship sc ON sc.Scholarship_ID = a.Scholarship_ID
JOIN Financial_Aid fa   ON fa.Aid_ID = a.Aid_ID
JOIN Sponsors sp        ON sp.Sponsor_ID = fa.Sponsor_ID
JOIN Academic_Terms t   ON t.Term_ID = a.Term_ID
JOIN Evaluators e       ON e.Evaluator_ID = a.Evaluator_ID
WHERE a.Application_ID = ?
"""


def get_application(application_id):
    """Full detail: joined names, checklist summary, disbursement totals,
    remaining balance and the eligibility screening result."""
    with db.get_db() as conn:
        row = conn.execute(_DETAIL_SQL, [application_id]).fetchone()
        if row is None:
            raise NotFoundError(f"Application '{application_id}' not found.")
        detail = _build_detail(dict(row))
        detail["Requirement_Summary"] = _requirement_summary(conn, application_id)
        disbursed_count, disbursed_total = _disbursement_totals(conn, application_id)

    detail["Disbursement_Summary"] = {
        "count": disbursed_count,
        "total_amount": disbursed_total,
    }
    detail["Balance"] = {
        "award_amount": detail["Award_Amount"],
        "disbursed": disbursed_total,
        "remaining": (None if detail["Award_Amount"] is None
                      else round(detail["Award_Amount"] - disbursed_total, 2)),
    }
    detail["Screening"] = eligibility_service.screen_application(application_id)
    return detail


def _build_detail(row):
    """Reshape the flat JOIN row into nested dicts (cleaner JSON)."""
    scholarship = None
    if row["Sch_ID"] is not None:
        scholarship = {
            "Scholarship_ID": row["Sch_ID"],
            "Scholarship_Name": row["Scholarship_Name"],
            "Scholarship_Type": row["Scholarship_Type"],
        }
    return {
        "Application_ID": row["Application_ID"],
        "Application_Date": row["Application_Date"],
        "Status": row["Status"],
        "Award_Amount": row["Award_Amount"],
        "Previous_Application_ID": row["Previous_Application_ID"],
        "Student": {
            "Student_ID": row["Student_ID"],
            "Student_Name": row["Student_Name"],
            "Program": row["Program"],
            "Year_Level": row["Year_Level"],
            "Email": row["Email"],
            "Contact_No": row["Contact_No"],
            "Household_Income": row["Household_Income"],
            "GPA": row["GPA"],
        },
        "Scholarship": scholarship,
        "Financial_Aid": {
            "Aid_ID": row["Aid_ID"],
            "Aid_Type": row["Aid_Type"],
            "Aid_Description": row["Aid_Description"],
            "Sponsor_ID": row["Sponsor_ID"],
            "Sponsor_Name": row["Sponsor_Name"],
        },
        "Term": {
            "Term_ID": row["Term_ID"],
            "Term_Name": row["Term_Name"],
            "Academic_Year": row["Academic_Year"],
        },
        "Evaluator": {
            "Evaluator_ID": row["Evaluator_ID"],
            "Evaluator_Name": row["Evaluator_Name"],
        },
    }


def _requirement_summary(conn, application_id):
    """Checklist counters, e.g. total 4 / verified 4 / all verified True."""
    rows = conn.execute(
        """SELECT Requirement_Status, COUNT(*) AS n
           FROM Application_Requirements
           WHERE Application_ID = ?
           GROUP BY Requirement_Status""",
        [application_id],
    ).fetchall()
    counts = {row["Requirement_Status"]: row["n"] for row in rows}  # dict comprehension
    total = sum(counts.values())
    return {
        "total": total,
        "Verified": counts.get("Verified", 0),
        "Submitted": counts.get("Submitted", 0),
        "Missing": counts.get("Missing", 0),
        "Pending": counts.get("Pending", 0),
        "all_verified": total > 0 and counts.get("Verified", 0) == total,
    }


def _disbursement_totals(conn, application_id):
    row = conn.execute(
        """SELECT COUNT(*) AS n, COALESCE(SUM(Disbursement_Amount), 0) AS total
           FROM Disbursements WHERE Application_ID = ?""",
        [application_id],
    ).fetchone()
    return row["n"], row["total"]


# ---------------------------------------------------------------------------
# Create / update / delete
# ---------------------------------------------------------------------------
def create_application(payload):
    """Submit a new application (always starts as Pending)."""
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object.")

    # Lifecycle guards - status and award are not settable at submission
    if payload.get("Status") not in (None, "Pending"):
        raise BusinessRuleError(
            "New applications must start with Status 'Pending'. Use "
            "POST /api/applications/<id>/review to approve or reject.")
    if payload.get("Award_Amount") not in (None, 0):
        raise BusinessRuleError(
            "Award_Amount cannot be set at submission. Use "
            "POST /api/applications/<id>/review after approval.")

    cleaned = validators.validate_application(payload)

    with db.get_db() as conn:
        _ensure_references_exist(conn, cleaned)
        _validate_renewal_link(conn, cleaned)

        if "Application_ID" not in cleaned:
            cleaned["Application_ID"] = base_service.generate_id("applications")
        elif base_service.row_exists("applications", cleaned["Application_ID"]):
            raise ConflictError(
                f"Application '{cleaned['Application_ID']}' already exists.")

        cleaned.setdefault("Application_Date", date.today().isoformat())
        # Every new application starts as Pending with no award yet
        cleaned["Status"] = "Pending"
        cleaned["Award_Amount"] = None
        base_service.insert_row("applications", cleaned)

    new_id = cleaned["Application_ID"]
    logger.info("Application %s submitted for student %s (Pending)",
                new_id, cleaned["Student_ID"])
    return get_application(new_id)


def update_application(application_id, payload):
    """Partial update of the descriptive fields.

    Status and Award_Amount are protected: they may only change through
    the review endpoint, keeping the lifecycle audit-clean.
    """
    current = base_service.get_row("applications", application_id)  # 404s

    if "Application_ID" in payload and payload["Application_ID"] != application_id:
        raise ValidationError(
            "Primary keys cannot be changed.",
            details={"fields": {"Application_ID":
                                f"Must stay '{application_id}'."}})
    if "Status" in payload and payload["Status"] != current["Status"]:
        raise BusinessRuleError(
            "Status can only be changed through "
            "POST /api/applications/<id>/review.")
    if "Award_Amount" in payload and payload["Award_Amount"] != current["Award_Amount"]:
        raise BusinessRuleError(
            "Award_Amount can only be changed through "
            "POST /api/applications/<id>/review.")

    cleaned = validators.validate_application(payload, partial=True)
    cleaned.pop("Status", None)
    cleaned.pop("Award_Amount", None)

    if cleaned:
        with db.get_db() as conn:
            _ensure_references_exist(conn, cleaned)
            # A changed student must still match the previous application
            _validate_renewal_link(conn, cleaned,
                                   student_id=cleaned.get("Student_ID",
                                                          current["Student_ID"]))
            base_service.update_row("applications", application_id, cleaned)

    logger.info("Application %s updated", application_id)
    return get_application(application_id)


def delete_application(application_id):
    """Delete an application. Checklist entries and disbursements cascade.

    Renewals that link to this application block deletion (FK constraint).
    """
    with db.get_db() as conn:
        counts = conn.execute(
            """SELECT
                 (SELECT COUNT(*) FROM Application_Requirements
                  WHERE Application_ID = ?) AS reqs,
                 (SELECT COUNT(*) FROM Disbursements
                  WHERE Application_ID = ?) AS disbs""",
            [application_id, application_id],
        ).fetchone()

    result = base_service.delete_row("applications", application_id)
    if counts["reqs"] or counts["disbs"]:
        result["message"] += (f" Cascade removed {counts['reqs']} requirement "
                              f"entries and {counts['disbs']} disbursements.")
    logger.info("Application %s deleted", application_id)
    return result


# ---------------------------------------------------------------------------
# Requirement checklist
# ---------------------------------------------------------------------------
def list_requirements(application_id):
    """The checklist of one application (requirement names joined in)."""
    base_service.get_row("applications", application_id)   # 404s

    with db.get_db() as conn:
        rows = conn.execute(
            """SELECT ar.Requirement_ID, r.Requirement_Name,
                      ar.Requirement_Status, ar.Submitted_Date
               FROM Application_Requirements ar
               JOIN Requirements r ON r.Requirement_ID = ar.Requirement_ID
               WHERE ar.Application_ID = ?
               ORDER BY ar.Requirement_ID""",
            [application_id],
        ).fetchall()

    data = [dict(row) for row in rows]
    verified = sum(1 for item in data if item["Requirement_Status"] == "Verified")
    return {
        "Application_ID": application_id,
        "count": len(data),
        "all_verified": len(data) > 0 and verified == len(data),
        "data": data,
    }


def attach_requirement(application_id, payload):
    """Add a requirement to the checklist, or update it if already attached."""
    cleaned = validators.validate_requirement_entry(payload)

    with db.get_db() as conn:
        base_service.get_row("applications", application_id)   # 404s

        if not base_service.row_exists("requirements", cleaned["Requirement_ID"]):
            raise ValidationError(
                "Unknown requirement.",
                details={"fields": {"Requirement_ID":
                        f"Requirement '{cleaned['Requirement_ID']}' does not exist."}})

        existing = conn.execute(
            """SELECT 1 FROM Application_Requirements
               WHERE Application_ID = ? AND Requirement_ID = ?""",
            [application_id, cleaned["Requirement_ID"]],
        ).fetchone()

        if existing:
            conn.execute(
                """UPDATE Application_Requirements
                   SET Requirement_Status = ?, Submitted_Date = ?
                   WHERE Application_ID = ? AND Requirement_ID = ?""",
                [cleaned["Requirement_Status"], cleaned.get("Submitted_Date"),
                 application_id, cleaned["Requirement_ID"]],
            )
            action = "updated"
        else:
            conn.execute(
                """INSERT INTO Application_Requirements
                   (Application_ID, Requirement_ID, Requirement_Status, Submitted_Date)
                   VALUES (?, ?, ?, ?)""",
                [application_id, cleaned["Requirement_ID"],
                 cleaned["Requirement_Status"], cleaned.get("Submitted_Date")],
            )
            action = "attached"

    logger.info("Requirement %s %s to application %s (%s)",
                cleaned["Requirement_ID"], action, application_id,
                cleaned["Requirement_Status"])
    return {
        "message": (f"Requirement {cleaned['Requirement_ID']} {action} "
                    f"with status '{cleaned['Requirement_Status']}'."),
        "data": list_requirements(application_id),
    }


def remove_requirement(application_id, requirement_id):
    """Remove one requirement from the checklist."""
    base_service.get_row("applications", application_id)       # 404s

    with db.get_db() as conn:
        existing = conn.execute(
            """SELECT 1 FROM Application_Requirements
               WHERE Application_ID = ? AND Requirement_ID = ?""",
            [application_id, requirement_id],
        ).fetchone()
        if existing is None:
            raise NotFoundError(
                f"Requirement '{requirement_id}' is not attached to "
                f"application '{application_id}'.")
        conn.execute(
            """DELETE FROM Application_Requirements
               WHERE Application_ID = ? AND Requirement_ID = ?""",
            [application_id, requirement_id],
        )

    logger.info("Requirement %s removed from application %s",
                requirement_id, application_id)
    return {
        "message": f"Requirement {requirement_id} removed from application "
                   f"{application_id}.",
        "data": list_requirements(application_id),
    }


# ---------------------------------------------------------------------------
# Review (approve / reject) and renewal
# ---------------------------------------------------------------------------
def review_application(application_id, payload):
    """Evaluator decision: approve (award required) or reject (award -> 0)."""
    reviewed = validators.validate_review(payload)

    with db.get_db() as conn:
        row = conn.execute(
            "SELECT Status FROM Applications WHERE Application_ID = ?",
            [application_id],
        ).fetchone()
        if row is None:
            raise NotFoundError(f"Application '{application_id}' not found.")

        # [Unit II] Control flow: state machine with if / elif
        if row["Status"] != "Pending":
            raise ConflictError(
                f"Application {application_id} is already {row['Status']}. "
                f"Only Pending applications can be reviewed.")

        if reviewed["action"] == "approve":
            _ensure_all_requirements_verified(conn, application_id)
            conn.execute(
                """UPDATE Applications
                   SET Status = 'Approved', Award_Amount = ?
                   WHERE Application_ID = ?""",
                [reviewed["award_amount"], application_id],
            )
            message = (f"Application {application_id} APPROVED with award "
                       f"PHP {format_money(reviewed['award_amount'])}.")
        else:
            conn.execute(
                """UPDATE Applications
                   SET Status = 'Rejected', Award_Amount = 0
                   WHERE Application_ID = ?""",
                [application_id],
            )
            message = f"Application {application_id} REJECTED (award set to 0)."

    logger.info("REVIEW %s -> %s", application_id, reviewed["action"].upper())

    detail = get_application(application_id)
    response = {"message": message, "data": detail}

    # Case-study limitation kept on purpose: eligibility rules are stored but
    # not enforced - so we warn instead of blocking when screening fails.
    if reviewed["action"] == "approve" and detail["Screening"]["eligible"] is False:
        response["screening_warning"] = (
            "Approved even though the student does not meet the scholarship's "
            "GPA / income limits (rules are stored but not automatically enforced).")
    return response


def _ensure_all_requirements_verified(conn, application_id):
    """Approval rule: every attached requirement must be Verified."""
    rows = conn.execute(
        """SELECT ar.Requirement_ID, r.Requirement_Name, ar.Requirement_Status
           FROM Application_Requirements ar
           JOIN Requirements r ON r.Requirement_ID = ar.Requirement_ID
           WHERE ar.Application_ID = ?
             AND ar.Requirement_Status != 'Verified'""",
        [application_id],
    ).fetchall()

    if rows:
        unverified = [
            {"Requirement_ID": row["Requirement_ID"],
             "Requirement_Name": row["Requirement_Name"],
             "Requirement_Status": row["Requirement_Status"]}
            for row in rows
        ]
        raise BusinessRuleError(
            "Cannot approve: not every attached requirement is Verified.",
            details={"unverified_requirements": unverified})


def renew_application(application_id, payload):
    """Create a renewal application linked to this one (same student)."""
    cleaned = validators.validate_renewal(payload)

    with db.get_db() as conn:
        source = conn.execute(
            "SELECT * FROM Applications WHERE Application_ID = ?",
            [application_id],
        ).fetchone()
        if source is None:
            raise NotFoundError(f"Application '{application_id}' not found.")

        if source["Status"] != "Approved":
            raise BusinessRuleError(
                "Only Approved applications can be renewed.")

        if not base_service.row_exists("terms", cleaned["Term_ID"]):
            raise ValidationError(
                "Unknown term.",
                details={"fields": {"Term_ID":
                        f"Term '{cleaned['Term_ID']}' does not exist."}})

        if cleaned["Term_ID"] == source["Term_ID"]:
            raise ConflictError(
                "A renewal must target a different academic term "
                f"(source application is already in term {source['Term_ID']}).")

        evaluator_id = cleaned.get("Evaluator_ID") or source["Evaluator_ID"]
        if not base_service.row_exists("evaluators", evaluator_id):
            raise ValidationError(
                "Unknown evaluator.",
                details={"fields": {"Evaluator_ID":
                        f"Evaluator '{evaluator_id}' does not exist."}})

        new_id = base_service.generate_id("applications")
        conn.execute(
            """INSERT INTO Applications
               (Application_ID, Student_ID, Scholarship_ID, Aid_ID, Term_ID,
                Evaluator_ID, Previous_Application_ID, Application_Date,
                Status, Award_Amount)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending', NULL)""",
            [new_id, source["Student_ID"], source["Scholarship_ID"],
             source["Aid_ID"], cleaned["Term_ID"], evaluator_id,
             application_id, date.today().isoformat()],
        )

    logger.info("Application %s renewed as %s (term %s)",
                application_id, new_id, cleaned["Term_ID"])
    return {
        "message": (f"Renewal application {new_id} created from "
                    f"{application_id} for term {cleaned['Term_ID']}."),
        "data": get_application(new_id),
    }


# ---------------------------------------------------------------------------
# Shared FK helpers
# ---------------------------------------------------------------------------
def _ensure_references_exist(conn, cleaned):
    """Verify that every referenced row really exists (nice 422 messages)."""
    checks = [
        ("Student_ID", "students", "Student"),
        ("Scholarship_ID", "scholarships", "Scholarship"),
        ("Aid_ID", "financial_aids", "Financial aid"),
        ("Term_ID", "terms", "Term"),
        ("Evaluator_ID", "evaluators", "Evaluator"),
    ]
    errors = {}
    for field, entity, label in checks:
        value = cleaned.get(field)
        if value is None:
            continue
        if not base_service.row_exists(entity, value):
            errors[field] = f"{label} '{value}' does not exist."
    if errors:
        raise ValidationError("Application references records that do not exist.",
                              details={"fields": errors})


def _validate_renewal_link(conn, cleaned, student_id=None):
    """A Previous_Application_ID must exist, belong to the same student,
    and cannot be the application itself."""
    previous_id = cleaned.get("Previous_Application_ID")
    if previous_id is None:
        return
    if previous_id == cleaned.get("Application_ID"):
        raise BusinessRuleError(
            "An application cannot be its own previous application.")

    row = conn.execute(
        "SELECT Student_ID FROM Applications WHERE Application_ID = ?",
        [previous_id],
    ).fetchone()
    if row is None:
        raise ValidationError(
            "Invalid renewal link.",
            details={"fields": {"Previous_Application_ID":
                    f"Application '{previous_id}' does not exist."}})

    owner = student_id or cleaned.get("Student_ID")
    if owner is not None and row["Student_ID"] != owner:
        raise BusinessRuleError(
            "Previous_Application_ID must belong to the same student.")
