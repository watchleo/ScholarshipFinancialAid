"""Student management: CRUD + listing a student's applications."""

from database import db
from services import base_service
from utils import validators
from utils.app_logger import get_logger
from utils.exceptions import ValidationError

logger = get_logger("students")


def list_students(search=None, program=None, year_level=None):
    """List students; optional filters: search (name/email), program, year."""
    conditions, params = [], []

    if search:
        # LIKE is case-insensitive for ASCII letters in SQLite
        conditions.append("(Student_Name LIKE ? OR Email LIKE ?)")
        like = f"%{search.strip()}%"
        params.extend([like, like])
    if program:
        conditions.append("Program = ?")
        params.append(program.strip())
    if year_level:
        conditions.append("Year_Level = ?")
        params.append(year_level.strip())

    where = " AND ".join(conditions) if conditions else None
    data = base_service.list_rows("students", where=where, params=params)

    filters = {k: v for k, v in {"search": search, "program": program,
                                 "year_level": year_level}.items() if v}
    return {"count": len(data), "filters": filters, "data": data}


def get_student(student_id):
    return base_service.get_row("students", student_id)


def create_student(payload):
    """Validate + insert a student; the ID is auto-generated when missing."""
    cleaned = validators.validate_student(payload)

    if "Student_ID" not in cleaned:
        cleaned["Student_ID"] = base_service.generate_id("students")
    elif base_service.row_exists("students", cleaned["Student_ID"]):
        from utils.exceptions import ConflictError
        raise ConflictError(f"Student '{cleaned['Student_ID']}' already exists.")

    row = base_service.insert_row("students", cleaned)
    logger.info("Created student %s (%s)", row["Student_ID"], row["Student_Name"])
    return row


def update_student(student_id, payload):
    """Partial update; only the fields sent in the payload are changed."""
    current = base_service.get_row("students", student_id)   # 404 when missing

    if "Student_ID" in payload and payload["Student_ID"] != student_id:
        raise ValidationError(
            "Primary keys cannot be changed.",
            details={"fields": {"Student_ID": f"Must stay '{student_id}'."}},
        )

    cleaned = validators.validate_student(payload, partial=True)
    row = base_service.update_row("students", student_id, cleaned)
    logger.info("Updated student %s", student_id)
    return row


def delete_student(student_id):
    """Delete a student (blocked with 409 while applications reference them)."""
    result = base_service.delete_row("students", student_id)
    logger.info("Deleted student %s", student_id)
    return result


def get_student_applications(student_id):
    """One student's applications plus a small per-status summary."""
    student = base_service.get_row("students", student_id)   # 404 when missing

    # Reuse the application listing (JOINs names in) - modules working together
    from services import application_service
    result = application_service.list_applications(student_id=student_id)
    applications = result["data"]

    # [Unit II] dict comprehension + sum built-in
    by_status = {}
    for app in applications:
        by_status[app["Status"]] = by_status.get(app["Status"], 0) + 1
    total_awarded = sum(
        app["Award_Amount"] or 0 for app in applications if app["Status"] == "Approved"
    )

    return {
        "student": student,
        "count": len(applications),
        "summary": {
            "by_status": by_status,
            "total_awarded": total_awarded,
        },
        "data": applications,
    }
