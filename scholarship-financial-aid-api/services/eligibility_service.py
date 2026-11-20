"""Eligibility screening (GPA / household income vs scholarship limits).

Case-study limitation, honored on purpose:
    "Eligibility rules (GPA/income limits, slots, sponsor budget) are
     stored but NOT automatically enforced."
The API therefore SCREENS and reports the result, but never blocks an
application on eligibility grounds - the evaluator makes the call.

[Unit II] Relational (<=), equality (==) and logical (and) operators all
appear in _evaluate().
"""

from services import base_service


def screen_student(scholarship_id, student_id):
    """Screen one student against one scholarship's stored limits."""
    scholarship = base_service.get_row("scholarships", scholarship_id)  # 404s
    student = base_service.get_row("students", student_id)              # 404s
    return _evaluate(student, scholarship)


def screen_application(application_id):
    """Screen the student of one application against its scholarship."""
    application = base_service.get_row("applications", application_id)  # 404s
    student = base_service.get_row("students", application["Student_ID"])

    scholarship = None
    if application["Scholarship_ID"] is not None:
        scholarship = base_service.get_row("scholarships", application["Scholarship_ID"])
    return _evaluate(student, scholarship)


def _evaluate(student, scholarship):
    """Compare GPA and household income with the scholarship limits."""
    if scholarship is None:
        return {
            "eligible": None,
            "scholarship_id": None,
            "checks": [],
            "note": "This application is not tied to a scholarship program, "
                    "so no GPA / household-income limits apply.",
        }

    gpa_ok = student["GPA"] <= scholarship["Max_GPA_Allowed"]
    income_ok = student["Household_Income"] <= scholarship["Max_Household_Income"]
    eligible = gpa_ok and income_ok        # logical AND of both checks

    checks = [
        {
            "rule": "GPA",
            "student_value": student["GPA"],
            "limit": scholarship["Max_GPA_Allowed"],
            "passed": gpa_ok,
            "detail": f"GPA {student['GPA']:.2f} <= max {scholarship['Max_GPA_Allowed']:.2f}",
        },
        {
            "rule": "Household income",
            "student_value": student["Household_Income"],
            "limit": scholarship["Max_Household_Income"],
            "passed": income_ok,
            "detail": (f"Income PHP {student['Household_Income']:,.2f} <= max "
                       f"PHP {scholarship['Max_Household_Income']:,.2f}"),
        },
    ]

    if eligible:
        note = "Student meets both scholarship limits."
    else:
        note = ("Student does NOT meet the scholarship limits. Flagged for the "
                "evaluator - per the case study, eligibility rules are stored "
                "but not automatically enforced.")
    return {
        "eligible": eligible,
        "scholarship_id": scholarship["Scholarship_ID"],
        "scholarship_name": scholarship["Scholarship_Name"],
        "checks": checks,
        "note": note,
    }
