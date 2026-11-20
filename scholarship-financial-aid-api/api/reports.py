"""Reports and file exports."""

from typing import Annotated

from fastapi import APIRouter, Body

from services import report_service

router = APIRouter(prefix="/api", tags=["Reports"])


@router.get("/reports/summary")
def summary():
    return report_service.summary()


@router.get("/reports/applications")
def applications_by_term(term_id: str | None = None):
    return report_service.applications_by_term(term_id=(term_id or "").strip().upper() or None)


@router.get("/reports/disbursements")
def disbursement_report(term_id: str | None = None):
    return report_service.disbursement_report(term_id=(term_id or "").strip().upper() or None)


@router.get("/reports/sponsors")
def sponsor_report():
    return report_service.sponsor_report()


@router.get("/reports/scholarships")
def scholarship_report():
    return report_service.scholarship_report()


@router.post("/export", status_code=201)
def export(payload: Annotated[dict, Body(examples=[{"entity": "applications", "format": "csv"}])]):
    """Export one entity to a CSV or JSON file in data/exports/."""
    return report_service.export_entity(payload)


@router.get("/exports")
def list_exports():
    return report_service.list_export_files()
