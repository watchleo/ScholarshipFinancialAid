"""Disbursement tracking (multi-installment releases per application).

Business rules:
  * disbursements can only be recorded for APPROVED applications;
  * per the case-study limitation, the cumulative amount is NOT hard-validated
    against Award_Amount - exceeding it is allowed but returned as a warning.
"""

from database import db
from services import base_service
from utils import validators
from utils.app_logger import get_logger
from utils.exceptions import BusinessRuleError, NotFoundError
from utils.formatters import format_money

logger = get_logger("disbursements")

_LIST_SQL = """
SELECT d.Disbursement_ID, d.Application_ID, d.Disbursement_Date,
       d.Disbursement_Amount, d.Payment_Method, d.Payment_Reference_No,
       d.Disbursement_Note, a.Status AS Application_Status,
       s.Student_ID, s.Student_Name
FROM Disbursements d
JOIN Applications a ON a.Application_ID = d.Application_ID
JOIN Students s      ON s.Student_ID = a.Student_ID
"""


def list_disbursements(application_id=None, payment_method=None):
    """All disbursements, optionally filtered by application / method."""
    conditions, params, applied = [], [], {}

    if application_id:
        conditions.append("d.Application_ID = ?")
        params.append(str(application_id).strip().upper())
        applied["application_id"] = params[-1]
    if payment_method:
        method = payment_method.strip()
        if method not in validators.PAYMENT_METHODS:
            from utils.exceptions import ValidationError
            raise ValidationError(
                "Invalid payment_method filter.",
                details={"fields": {"payment_method":
                        "must be one of: "
                        + ", ".join(validators.PAYMENT_METHODS)}})
        conditions.append("d.Payment_Method = ?")
        params.append(method)
        applied["payment_method"] = method

    sql = _LIST_SQL
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY d.Disbursement_Date, d.Disbursement_ID"

    with db.get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    data = [dict(row) for row in rows]
    return {"count": len(data), "filters": applied, "data": data}


def get_disbursement(disbursement_id):
    """One disbursement; raises NotFoundError (404)."""
    with db.get_db() as conn:
        row = conn.execute(_LIST_SQL + " WHERE d.Disbursement_ID = ?",
                           [disbursement_id]).fetchone()
    if row is None:
        raise NotFoundError(f"Disbursement '{disbursement_id}' not found.")
    return dict(row)


def create_disbursement(application_id, payload):
    """Record a disbursement (installment) for an approved application."""
    cleaned = validators.validate_disbursement(payload)

    with db.get_db() as conn:
        application = conn.execute(
            "SELECT * FROM Applications WHERE Application_ID = ?",
            [application_id],
        ).fetchone()
        if application is None:
            raise NotFoundError(f"Application '{application_id}' not found.")

        if application["Status"] != "Approved":
            raise BusinessRuleError(
                "Disbursements can only be recorded for Approved applications "
                f"(this one is {application['Status']}).")

        if "Disbursement_ID" not in cleaned:
            cleaned["Disbursement_ID"] = base_service.generate_id("disbursements")
        elif base_service.row_exists("disbursements", cleaned["Disbursement_ID"]):
            from utils.exceptions import ConflictError
            raise ConflictError(
                f"Disbursement '{cleaned['Disbursement_ID']}' already exists.")

        cleaned["Application_ID"] = application_id
        base_service.insert_row("disbursements", cleaned)

        totals = conn.execute(
            """SELECT COUNT(*) AS n, COALESCE(SUM(Disbursement_Amount), 0) AS total
               FROM Disbursements WHERE Application_ID = ?""",
            [application_id],
        ).fetchone()
        disbursed_total, count = totals["total"], totals["n"]

    disbursement_id = cleaned["Disbursement_ID"]
    amount = cleaned["Disbursement_Amount"]
    award = application["Award_Amount"]
    logger.info("Disbursement %s recorded for %s: PHP %s via %s",
                disbursement_id, application_id, format_money(amount),
                cleaned["Payment_Method"])

    response = {
        "message": (f"Disbursement {disbursement_id} recorded for application "
                    f"{application_id} (PHP {format_money(amount)})."),
        "data": get_disbursement(disbursement_id),
        "application_totals": {
            "award_amount": award,
            "disbursement_count": count,
            "disbursed_total": disbursed_total,
            "remaining": (None if award is None
                          else round(award - disbursed_total, 2)),
        },
    }

    # Case-study limitation: no automatic validation against Award_Amount.
    # We keep the data but clearly flag the overshoot.
    if award is not None and disbursed_total > award:
        response["warning"] = (
            f"Total disbursed (PHP {format_money(disbursed_total)}) now exceeds "
            f"the approved award (PHP {format_money(award)}). Recorded anyway - "
            "per the case study, disbursements are not automatically validated "
            "against Award_Amount.")
    return response


def delete_disbursement(disbursement_id):
    """Delete a disbursement (e.g. to correct a data-entry mistake)."""
    result = base_service.delete_row("disbursements", disbursement_id)
    logger.info("Disbursement %s deleted", disbursement_id)
    return result
