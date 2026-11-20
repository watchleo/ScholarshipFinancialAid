"""Input validation for every API payload.

[Unit II] highlights in this module:
  * Functions      - small "cleaner" functions, one job each, raising
                     ValueError with a friendly message;
  * String manipulation - strip(), lower(), fullmatch(), join(), slicing;
  * Operators      - comparisons (<=, >=, !=), membership (in, not in),
                     logical operators (and, or, not);
  * Exceptions     - ValueError raised per field, collected into one
                     ValidationError (HTTP 422) for the whole payload.
"""

import re
from datetime import datetime

from utils.exceptions import ValidationError

# ---------------------------------------------------------------------------
# Constants (tuples = immutable ordered collections)
# ---------------------------------------------------------------------------
YEAR_LEVELS = ("1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year")
APPLICATION_STATUSES = ("Pending", "Approved", "Rejected")
REQUIREMENT_STATUSES = ("Submitted", "Verified", "Missing", "Pending")
PAYMENT_METHODS = ("Bank Transfer", "GCash", "Check", "Cash")
REVIEW_ACTIONS = ("approve", "reject")
EXPORT_FORMATS = ("csv", "json")
EXPORT_ENTITIES = (
    "students",
    "scholarships",
    "terms",
    "evaluators",
    "requirements",
    "sponsors",
    "financial_aids",
    "applications",
    "application_requirements",
    "disbursements",
)
ISO_DATE_FORMAT = "%Y-%m-%d"

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_PATTERN = re.compile(r"^[\d\-()+ ]{7,20}$")
ID_PATTERN = re.compile(r"^[A-Za-z]{1,4}\d{1,4}$")
YEAR_PATTERN = re.compile(r"^\d{4}-\d{4}$")


# ---------------------------------------------------------------------------
# Small "cleaner" functions (each returns the cleaned value or raises ValueError)
# ---------------------------------------------------------------------------
def clean_text(value, max_len=None, min_len=1):
    """Strip surrounding spaces and enforce length limits."""
    if value is None:
        raise ValueError("is required.")
    if not isinstance(value, str):
        raise ValueError("must be a string.")
    text = value.strip()
    if len(text) < min_len:
        raise ValueError("cannot be empty.")
    if max_len is not None and len(text) > max_len:
        raise ValueError(f"must be at most {max_len} characters long.")
    return text


def clean_id(value):
    """Validate an identifier like 'S001' or 'A007' (case-insensitive)."""
    if value is None:
        raise ValueError("is required.")
    if not isinstance(value, str):
        raise ValueError("must be a string.")
    text = value.strip().upper()
    if not ID_PATTERN.fullmatch(text):
        raise ValueError("must look like 'S001' (up to 4 letters followed by digits).")
    return text


def clean_email(value):
    """Normalize and validate an email address."""
    text = clean_text(value, max_len=120).lower()  # emails are case-insensitive
    if not EMAIL_PATTERN.fullmatch(text):
        raise ValueError("must be a valid email address (e.g. juan@university.edu.ph).")
    return text


def clean_phone(value):
    """Validate a Philippine-style contact number.

    Accepts digits, spaces, dashes and parentheses, e.g.
    '0917-111-2233' or '(02) 8123-4567'.
    """
    text = clean_text(value, max_len=20)
    if not PHONE_PATTERN.fullmatch(text):
        raise ValueError("may only contain digits, spaces, dashes and parentheses.")
    digit_count = sum(1 for ch in text if ch.isdigit())  # generator expression
    if not 7 <= digit_count <= 13:
        raise ValueError("must contain 7 to 13 digits.")
    return text


def clean_number(value):
    """Accept int/float (or numeric text) and return a float."""
    if isinstance(value, bool):  # bool is a subclass of int - reject it
        raise ValueError("must be a number.")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace(",", "")  # allow '25,000'
        try:
            return float(text)
        except ValueError:
            # 'raise ... from None' hides the confusing inner traceback
            raise ValueError("must be a number.") from None
    raise ValueError("must be a number.")


def clean_non_negative_money(value):
    """Money that may be zero but not negative."""
    amount = clean_number(value)
    if amount < 0:
        raise ValueError("cannot be negative.")
    return amount


def clean_positive_money(value):
    """Money that must be greater than zero."""
    amount = clean_number(value)
    if amount <= 0:
        raise ValueError("must be greater than zero.")
    return amount


def clean_gpa(value):
    """GPA on the Philippine 1.00 (highest) to 5.00 (lowest) scale."""
    gpa = clean_number(value)
    if not 1.0 <= gpa <= 5.0:  # relational + logical operators
        raise ValueError("must be between 1.00 and 5.00.")
    return gpa


def clean_int(value, minimum=None, maximum=None):
    """Whole number with optional bounds."""
    if isinstance(value, bool):
        raise ValueError("must be a whole number.")
    if isinstance(value, int):
        number = value
    elif isinstance(value, float) and value.is_integer():
        number = int(value)
    elif isinstance(value, str) and value.strip().isdigit():
        number = int(value.strip())
    else:
        raise ValueError("must be a whole number.")
    if minimum is not None and number < minimum:
        raise ValueError(f"must be at least {minimum}.")
    if maximum is not None and number > maximum:
        raise ValueError(f"must be at most {maximum}.")
    return number


def clean_choice(value, options):
    """Value must be one of the allowed options."""
    text = clean_text(value, max_len=40)
    if text not in options:  # membership operator
        raise ValueError(f"must be one of: {', '.join(options)}.")
    return text


def clean_date(value):
    """ISO date (YYYY-MM-DD); also normalizes '2025-6-10' -> '2025-06-10'."""
    text = clean_text(value, max_len=10)
    try:
        parsed = datetime.strptime(text, ISO_DATE_FORMAT)
    except ValueError:
        raise ValueError("must be a valid date in YYYY-MM-DD format.") from None
    return parsed.strftime(ISO_DATE_FORMAT)


def clean_academic_year(value):
    """Academic year in 'YYYY-YYYY' form, e.g. 2025-2026."""
    text = clean_text(value, max_len=9)
    if not YEAR_PATTERN.fullmatch(text):
        raise ValueError("must look like '2025-2026'.")
    return text


# ---------------------------------------------------------------------------
# Generic field-by-field validation loop shared by all entities
# ---------------------------------------------------------------------------
def _validate_entity(data, field_specs, partial=False):
    """Validate ``data`` against ``field_specs`` and return cleaned fields.

    ``field_specs`` maps a JSON field name -> (cleaner_function, required).
    With ``partial=True`` (used by PUT) missing keys are simply skipped.

    All field errors are collected first, then raised together as one
    ValidationError, so the client sees every problem at once.
    """
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")

    errors = {}
    cleaned = {}
    for field, (cleaner, required) in field_specs.items():
        if field not in data or data[field] is None:
            if required and not partial:
                errors[field] = "This field is required."
            continue
        try:
            cleaned[field] = cleaner(data[field])
        except ValueError as error:
            errors[field] = str(error)

    if errors:  # only raise once, with every field error included
        raise ValidationError(
            "Some fields failed validation.", details={"fields": errors}
        )
    return cleaned


# ---------------------------------------------------------------------------
# Entity validators (one per table exposed by the API)
# ---------------------------------------------------------------------------
def validate_student(data, partial=False):
    """Fields of the Students table."""
    return _validate_entity(
        data,
        {
            "Student_ID": (clean_id, False),
            "Student_Name": (lambda v: clean_text(v, max_len=100), True),
            "Program": (lambda v: clean_text(v, max_len=100), True),
            "Year_Level": (lambda v: clean_choice(v, YEAR_LEVELS), True),
            "Email": (clean_email, True),
            "Contact_No": (clean_phone, True),
            "Household_Income": (clean_non_negative_money, True),
            "GPA": (clean_gpa, True),
        },
        partial,
    )


def validate_scholarship(data, partial=False):
    """Fields of the Scholarship table."""
    return _validate_entity(
        data,
        {
            "Scholarship_ID": (clean_id, False),
            "Scholarship_Name": (lambda v: clean_text(v, max_len=100), True),
            "Scholarship_Type": (lambda v: clean_text(v, max_len=40), True),
            "Scholarship_Slots": (lambda v: clean_int(v, minimum=1), True),
            "Max_GPA_Allowed": (clean_gpa, True),
            "Max_Household_Income": (clean_non_negative_money, True),
        },
        partial,
    )


def validate_term(data, partial=False):
    """Fields of the Academic_Terms table."""
    return _validate_entity(
        data,
        {
            "Term_ID": (clean_id, False),
            "Term_Name": (lambda v: clean_text(v, max_len=40), True),
            "Academic_Year": (clean_academic_year, True),
        },
        partial,
    )


def validate_evaluator(data, partial=False):
    """Fields of the Evaluators table."""
    return _validate_entity(
        data,
        {
            "Evaluator_ID": (clean_id, False),
            "Evaluator_Name": (lambda v: clean_text(v, max_len=100), True),
        },
        partial,
    )


def validate_requirement(data, partial=False):
    """Fields of the Requirements table."""
    return _validate_entity(
        data,
        {
            "Requirement_ID": (clean_id, False),
            "Requirement_Name": (lambda v: clean_text(v, max_len=100), True),
        },
        partial,
    )


def validate_sponsor(data, partial=False):
    """Fields of the Sponsors table."""
    return _validate_entity(
        data,
        {
            "Sponsor_ID": (clean_id, False),
            "Sponsor_Name": (lambda v: clean_text(v, max_len=100), True),
            "Sponsor_Type": (lambda v: clean_text(v, max_len=60), True),
            "Sponsor_Email": (clean_email, True),
            "Sponsor_Contact_No": (clean_phone, True),
            "Sponsor_Budget": (clean_non_negative_money, True),
        },
        partial,
    )


def validate_financial_aid(data, partial=False):
    """Fields of the Financial_Aid table."""
    return _validate_entity(
        data,
        {
            "Aid_ID": (clean_id, False),
            "Sponsor_ID": (clean_id, True),
            "Aid_Type": (lambda v: clean_text(v, max_len=40), True),
            "Aid_Description": (lambda v: clean_text(v, max_len=200), True),
        },
        partial,
    )


def validate_application(data, partial=False):
    """Fields of the Applications table.

    Status and Award_Amount are NOT validated here on purpose: new
    applications always start as Pending, and the award is only set
    through the review endpoint (business rules in the service layer).
    """
    return _validate_entity(
        data,
        {
            "Application_ID": (clean_id, False),
            "Student_ID": (clean_id, True),
            "Scholarship_ID": (clean_id, False),
            "Aid_ID": (clean_id, True),
            "Term_ID": (clean_id, True),
            "Evaluator_ID": (clean_id, True),
            "Previous_Application_ID": (clean_id, False),
            "Application_Date": (clean_date, False),
        },
        partial,
    )


def validate_requirement_entry(data, partial=False):
    """One row of the Application_Requirements checklist."""
    cleaned = _validate_entity(
        data,
        {
            "Requirement_ID": (clean_id, True),
            "Requirement_Status": (lambda v: clean_choice(v, REQUIREMENT_STATUSES), True),
            "Submitted_Date": (clean_date, False),
        },
        partial,
    )

    # Cross-field rule: Verified / Submitted entries need a submission date
    # (the case-study data follows the same pattern).
    if cleaned.get("Requirement_Status") in ("Verified", "Submitted"):
        if "Submitted_Date" not in cleaned:
            raise ValidationError(
                "Requirement entry is incomplete.",
                details={
                    "fields": {
                        "Submitted_Date": "Required when Requirement_Status is "
                        "'Verified' or 'Submitted'."
                    }
                },
            )
    return cleaned


def validate_disbursement(data, partial=False):
    """Fields of the Disbursements table."""
    return _validate_entity(
        data,
        {
            "Disbursement_ID": (clean_id, False),
            "Disbursement_Date": (clean_date, True),
            "Disbursement_Amount": (clean_positive_money, True),
            "Payment_Method": (lambda v: clean_choice(v, PAYMENT_METHODS), True),
            "Payment_Reference_No": (lambda v: clean_text(v, max_len=40), True),
            "Disbursement_Note": (lambda v: clean_text(v, max_len=120), False),
        },
        partial,
    )


def validate_review(data):
    """Payload of POST /api/applications/<id>/review."""
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")

    errors = {}
    action = data.get("action")
    if not isinstance(action, str) or action.strip().lower() not in REVIEW_ACTIONS:
        errors["action"] = "must be 'approve' or 'reject'."
        raise ValidationError("Invalid review payload.", details={"fields": errors})

    result = {"action": action.strip().lower()}

    if result["action"] == "approve":
        try:
            result["award_amount"] = clean_positive_money(data.get("award_amount"))
        except ValueError as error:
            raise ValidationError(
                "Invalid review payload.",
                details={"fields": {"award_amount": str(error)}},
            )
    return result


def validate_renewal(data):
    """Payload of POST /api/applications/<id>/renew."""
    return _validate_entity(
        data,
        {
            "Term_ID": (clean_id, True),
            "Evaluator_ID": (clean_id, False),
        },
        partial=False,
    )


def validate_export(data):
    """Payload of POST /api/export."""
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")

    cleaned = _validate_entity(
        data,
        {
            "entity": (lambda v: clean_text(v, max_len=40), True),
            "format": (lambda v: clean_choice(v, EXPORT_FORMATS), False),
        },
        partial=False,
    )

    if cleaned["entity"] not in EXPORT_ENTITIES:
        raise ValidationError(
            "Unknown export entity.",
            details={
                "fields": {
                    "entity": f"must be one of: {', '.join(EXPORT_ENTITIES)}."
                }
            },
        )
    cleaned.setdefault("format", "csv")
    return cleaned
