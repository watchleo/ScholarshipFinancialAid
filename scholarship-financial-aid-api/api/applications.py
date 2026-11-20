"""Application submissions, reviews, requirement checklists and disbursements."""

from typing import Annotated

from fastapi import APIRouter, Body

from services import application_service, disbursement_service, eligibility_service

router = APIRouter(prefix="/api", tags=["Applications"])


@router.get("/applications")
def list_applications(
    status: str | None = None,
    student_id: str | None = None,
    scholarship_id: str | None = None,
    aid_id: str | None = None,
    term_id: str | None = None,
    evaluator_id: str | None = None,
    previous_application_id: str | None = None,
):
    return application_service.list_applications(
        status=status, student_id=student_id, scholarship_id=scholarship_id,
        aid_id=aid_id, term_id=term_id, evaluator_id=evaluator_id,
        previous_application_id=previous_application_id,
    )


@router.post("/applications", status_code=201)
def create_application(payload: Annotated[dict, Body(examples=[{
    "Student_ID": "S001", "Scholarship_ID": "SCH01", "Aid_ID": "FA01",
    "Term_ID": "T03", "Evaluator_ID": "E01",
}])]):
    """Submit an application for review. A new submission starts as Pending."""
    detail = application_service.create_application(payload)
    return {
        "message": f"Application {detail['Application_ID']} submitted successfully (status: Pending).",
        "data": detail,
    }


@router.get("/applications/{application_id}")
def get_application(application_id: str):
    return {"data": application_service.get_application(application_id.strip().upper())}


@router.put("/applications/{application_id}")
def update_application(application_id: str, payload: dict):
    """Update descriptive fields. Use the review endpoint to set status and award."""
    detail = application_service.update_application(application_id.strip().upper(), payload)
    return {"message": f"Application {detail['Application_ID']} updated successfully.", "data": detail}


@router.delete("/applications/{application_id}")
def delete_application(application_id: str):
    return application_service.delete_application(application_id.strip().upper())


@router.get("/applications/{application_id}/requirements")
def list_requirements(application_id: str):
    return application_service.list_requirements(application_id.strip().upper())


@router.post("/applications/{application_id}/requirements")
def attach_requirement(application_id: str, payload: Annotated[dict, Body(examples=[{
    "Requirement_ID": "R01", "Requirement_Status": "Verified", "Submitted_Date": "2026-06-14",
}])]):
    """Add or update an entry in the requirement checklist."""
    return application_service.attach_requirement(application_id.strip().upper(), payload)


@router.delete("/applications/{application_id}/requirements/{requirement_id}")
def remove_requirement(application_id: str, requirement_id: str):
    return application_service.remove_requirement(
        application_id.strip().upper(), requirement_id.strip().upper()
    )


@router.post("/applications/{application_id}/review")
def review_application(application_id: str, payload: Annotated[dict, Body(examples=[{
    "action": "approve", "award_amount": 25000,
}])]):
    """Approve a pending application with an award amount, or reject it."""
    return application_service.review_application(application_id.strip().upper(), payload)


@router.post("/applications/{application_id}/renew", status_code=201)
def renew_application(application_id: str, payload: Annotated[dict, Body(examples=[{"Term_ID": "T03"}])]):
    """Create a linked renewal application for another term."""
    return application_service.renew_application(application_id.strip().upper(), payload)


@router.get("/applications/{application_id}/screening")
def screen_application(application_id: str):
    return {"data": eligibility_service.screen_application(application_id.strip().upper())}


@router.get("/applications/{application_id}/disbursements")
def list_application_disbursements(application_id: str):
    return disbursement_service.list_disbursements(application_id=application_id.strip().upper())


@router.post("/applications/{application_id}/disbursements", status_code=201)
def create_disbursement(application_id: str, payload: Annotated[dict, Body(examples=[{
    "Disbursement_Date": "2026-07-15", "Disbursement_Amount": 12500,
    "Payment_Method": "Bank Transfer", "Payment_Reference_No": "DEMO-001",
}])]):
    """Record a payment installment for an approved application."""
    return disbursement_service.create_disbursement(application_id.strip().upper(), payload)


@router.get("/disbursements")
def list_disbursements(application_id: str | None = None, payment_method: str | None = None):
    return disbursement_service.list_disbursements(
        application_id=application_id, payment_method=payment_method,
    )


@router.get("/disbursements/{disbursement_id}")
def get_disbursement(disbursement_id: str):
    return {"data": disbursement_service.get_disbursement(disbursement_id.strip().upper())}


@router.delete("/disbursements/{disbursement_id}")
def delete_disbursement(disbursement_id: str):
    return disbursement_service.delete_disbursement(disbursement_id.strip().upper())
