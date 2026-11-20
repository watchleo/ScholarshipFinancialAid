"""Reports and file exports.

Aggregation queries (GROUP BY, SUM, COUNT, CASE WHEN) run in SQL; the
results are then reshaped in Python with loops, dict comprehensions and
f-strings ([Unit II] control flow, data structures, string formatting).
"""

from database import db
from services import base_service
from utils import exporters, validators
from utils.app_logger import get_logger
from utils.formatters import format_money

logger = get_logger("reports")


def summary():
    """High-level totals for the whole system."""
    counts = db.table_row_counts()

    with db.get_db() as conn:
        status_rows = conn.execute(
            """SELECT Status, COUNT(*) AS n,
                      COALESCE(SUM(Award_Amount), 0) AS total
               FROM Applications GROUP BY Status"""
        ).fetchall()
        disbursed_row = conn.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(Disbursement_Amount), 0) AS total "
            "FROM Disbursements"
        ).fetchone()

    # dict comprehension: {status: count} in one line
    by_status = {row["Status"]: row["n"] for row in status_rows}
    total_awarded = sum(row["total"] for row in status_rows
                        if row["Status"] == "Approved")
    total_disbursed = disbursed_row["total"]

    return {
        "records": counts,
        "total_records": sum(counts.values()),
        "applications_by_status": by_status,
        "approved": by_status.get("Approved", 0),
        "pending": by_status.get("Pending", 0),
        "rejected": by_status.get("Rejected", 0),
        "total_awarded": total_awarded,
        "total_awarded_formatted": f"PHP {format_money(total_awarded)}",
        "total_disbursed": total_disbursed,
        "total_disbursed_formatted": f"PHP {format_money(total_disbursed)}",
        "remaining_balance": round(total_awarded - total_disbursed, 2),
    }


def applications_by_term(term_id=None):
    """Applications, awards and disbursements grouped per academic term."""
    with db.get_db() as conn:
        if term_id:
            if not base_service.row_exists("terms", term_id):
                from utils.exceptions import NotFoundError
                raise NotFoundError(f"Term '{term_id}' not found.")
        rows = conn.execute(
            """
            SELECT t.Term_ID, t.Term_Name, t.Academic_Year,
                   COUNT(a.Application_ID) AS applications,
                   SUM(CASE WHEN a.Status = 'Approved' THEN 1 ELSE 0 END) AS approved,
                   SUM(CASE WHEN a.Status = 'Pending'  THEN 1 ELSE 0 END) AS pending,
                   SUM(CASE WHEN a.Status = 'Rejected' THEN 1 ELSE 0 END) AS rejected,
                   COALESCE(SUM(CASE WHEN a.Status = 'Approved'
                                     THEN a.Award_Amount END), 0) AS awarded
            FROM Academic_Terms t
            LEFT JOIN Applications a ON a.Term_ID = t.Term_ID
            GROUP BY t.Term_ID
            ORDER BY t.Term_ID
            """
        ).fetchall()

        disbursed_by_term = {
            row["Term_ID"]: row["total"]
            for row in conn.execute(
                """SELECT a.Term_ID, COALESCE(SUM(d.Disbursement_Amount), 0) AS total
                   FROM Disbursements d
                   JOIN Applications a ON a.Application_ID = d.Application_ID
                   GROUP BY a.Term_ID""")
        }

    data = []
    for row in rows:                       # [Unit II] loop + conditionals
        if term_id and row["Term_ID"] != term_id:
            continue
        awarded = row["awarded"]
        disbursed = disbursed_by_term.get(row["Term_ID"], 0)
        data.append({
            "Term_ID": row["Term_ID"],
            "Term": f"{row['Term_Name']} {row['Academic_Year']}",
            "applications": row["applications"],
            "approved": row["approved"],
            "pending": row["pending"],
            "rejected": row["rejected"],
            "awarded": awarded,
            "awarded_formatted": f"PHP {format_money(awarded)}",
            "disbursed": disbursed,
            "disbursed_formatted": f"PHP {format_money(disbursed)}",
            "balance": round(awarded - disbursed, 2),
        })
    return {"count": len(data), "data": data}


def disbursement_report(term_id=None):
    """Per-application award vs actually disbursed, plus totals + warnings."""
    with db.get_db() as conn:
        rows = conn.execute(
            """
            SELECT a.Application_ID, s.Student_Name,
                   t.Term_ID, t.Term_Name, t.Academic_Year,
                   a.Status, a.Award_Amount,
                   COALESCE((SELECT SUM(d.Disbursement_Amount)
                             FROM Disbursements d
                             WHERE d.Application_ID = a.Application_ID), 0) AS disbursed
            FROM Applications a
            JOIN Students s       ON s.Student_ID = a.Student_ID
            JOIN Academic_Terms t ON t.Term_ID = a.Term_ID
            ORDER BY a.Application_Date, a.Application_ID
            """
        ).fetchall()

    data, warnings = [], []
    for row in rows:
        if term_id and row["Term_ID"] != term_id:
            continue
        award = row["Award_Amount"] or 0
        disbursed = row["disbursed"]
        entry = {
            "Application_ID": row["Application_ID"],
            "Student_Name": row["Student_Name"],
            "Term": f"{row['Term_Name']} {row['Academic_Year']}",
            "Status": row["Status"],
            "award_amount": row["Award_Amount"],
            "disbursed": disbursed,
            "balance": round(award - disbursed, 2),
        }
        data.append(entry)
        if row["Status"] == "Approved" and disbursed > award:
            warnings.append(
                f"{row['Application_ID']}: disbursed PHP {format_money(disbursed)} "
                f"exceeds award PHP {format_money(award)}")

    total_award = sum(item["award_amount"] or 0 for item in data)
    total_disbursed = sum(item["disbursed"] for item in data)
    return {
        "count": len(data),
        "totals": {
            "award_amount": total_award,
            "disbursed": total_disbursed,
            "balance": round(total_award - total_disbursed, 2),
        },
        "warnings": warnings,
        "data": data,
    }


def sponsor_report():
    """Sponsor budget vs committed/pending assistance (via financial aids)."""
    with db.get_db() as conn:
        rows = conn.execute(
            """
            SELECT sp.Sponsor_ID, sp.Sponsor_Name, sp.Sponsor_Type,
                   sp.Sponsor_Budget,
                   COALESCE(SUM(CASE WHEN a.Status = 'Approved'
                                     THEN a.Award_Amount END), 0) AS committed,
                   COALESCE(SUM(CASE WHEN a.Status = 'Pending' THEN 1 ELSE 0 END), 0)
                       AS pending_applications
            FROM Sponsors sp
            LEFT JOIN Financial_Aid fa ON fa.Sponsor_ID = sp.Sponsor_ID
            LEFT JOIN Applications a  ON a.Aid_ID = fa.Aid_ID
            GROUP BY sp.Sponsor_ID
            ORDER BY sp.Sponsor_ID
            """
        ).fetchall()

    data = []
    for row in rows:
        budget, committed = row["Sponsor_Budget"], row["committed"]
        remaining = budget - committed
        utilization = (committed / budget * 100) if budget else 0.0
        data.append({
            "Sponsor_ID": row["Sponsor_ID"],
            "Sponsor_Name": row["Sponsor_Name"],
            "Sponsor_Type": row["Sponsor_Type"],
            "budget": budget,
            "budget_formatted": f"PHP {format_money(budget)}",
            "committed": committed,
            "committed_formatted": f"PHP {format_money(committed)}",
            "remaining_budget": remaining,
            "pending_applications": row["pending_applications"],
            "budget_utilization_pct": round(utilization, 2),
        })
    return {"count": len(data), "data": data}


def scholarship_report():
    """Slots used per scholarship (approved vs pending applications)."""
    with db.get_db() as conn:
        rows = conn.execute(
            """
            SELECT sc.Scholarship_ID, sc.Scholarship_Name, sc.Scholarship_Type,
                   sc.Scholarship_Slots, sc.Max_GPA_Allowed,
                   sc.Max_Household_Income,
                   SUM(CASE WHEN a.Status = 'Approved' THEN 1 ELSE 0 END) AS approved,
                   SUM(CASE WHEN a.Status = 'Pending'  THEN 1 ELSE 0 END) AS pending
            FROM Scholarship sc
            LEFT JOIN Applications a ON a.Scholarship_ID = sc.Scholarship_ID
            GROUP BY sc.Scholarship_ID
            ORDER BY sc.Scholarship_ID
            """
        ).fetchall()

    data = []
    for row in rows:
        slots, approved = row["Scholarship_Slots"], row["approved"] or 0
        data.append({
            "Scholarship_ID": row["Scholarship_ID"],
            "Scholarship_Name": row["Scholarship_Name"],
            "Scholarship_Type": row["Scholarship_Type"],
            "slots": slots,
            "approved_applications": approved,
            "pending_applications": row["pending"] or 0,
            "remaining_slots": slots - approved,
            "slot_utilization_pct": round(approved / slots * 100, 2),
            "Max_GPA_Allowed": row["Max_GPA_Allowed"],
            "Max_Household_Income": row["Max_Household_Income"],
        })
    return {"count": len(data), "data": data}


def export_entity(payload):
    """Write one entity to a CSV/JSON file inside data/exports/."""
    cleaned = validators.validate_export(payload)
    rows = base_service.list_rows(cleaned["entity"])
    result = exporters.export_to_file(cleaned["entity"], rows, cleaned["format"])
    logger.info("Exported %d %s rows to %s",
                result["rows"], cleaned["entity"], result["file"])
    return result


def list_export_files():
    """Previously exported files (newest first)."""
    return {"count": len(exporters.list_export_files()),
            "data": exporters.list_export_files()}
