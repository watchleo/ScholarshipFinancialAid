"""Report endpoints + CSV/JSON file exports."""

from flask import Blueprint, jsonify, request

from services import report_service
from api.common import get_json_body

reports_bp = Blueprint("reports", __name__)


@reports_bp.get("/api/reports/summary")
def summary():
    """GET - system-wide totals: counts per table, totals per status."""
    return jsonify(report_service.summary())


@reports_bp.get("/api/reports/applications")
def applications_by_term():
    """GET - applications, awards and disbursements per academic term.
    Optional filter: ?term_id=T01"""
    return jsonify(report_service.applications_by_term(
        term_id=(request.args.get("term_id") or "").strip().upper() or None))


@reports_bp.get("/api/reports/disbursements")
def disbursement_report():
    """GET - award vs disbursed per application, with warnings on overshoot.
    Optional filter: ?term_id=T01"""
    return jsonify(report_service.disbursement_report(
        term_id=(request.args.get("term_id") or "").strip().upper() or None))


@reports_bp.get("/api/reports/sponsors")
def sponsor_report():
    """GET - sponsor budget vs committed assistance (via financial aids)."""
    return jsonify(report_service.sponsor_report())


@reports_bp.get("/api/reports/scholarships")
def scholarship_report():
    """GET - slot utilization per scholarship program."""
    return jsonify(report_service.scholarship_report())


@reports_bp.post("/api/export")
def export():
    """POST - export one entity to data/exports/ as CSV or JSON.

    Body: {"entity": "applications", "format": "csv"}
    """
    return jsonify(report_service.export_entity(get_json_body())), 201


@reports_bp.get("/api/exports")
def list_exports():
    """GET - list previously exported files (newest first)."""
    return jsonify(report_service.list_export_files())
