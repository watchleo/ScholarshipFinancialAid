"""HTTP endpoints for scholarships and student eligibility screening."""

from typing import Annotated

from fastapi import APIRouter, Body, Query

from services import catalog_service, eligibility_service
from utils.exceptions import ValidationError

router = APIRouter(prefix="/api/scholarships", tags=["Scholarships"])

SCHOLARSHIP_EXAMPLE = {
    "Scholarship_Name": "Community Leadership Scholarship",
    "Scholarship_Type": "Merit-Based",
    "Scholarship_Slots": 10,
    "Max_GPA_Allowed": 2.0,
    "Max_Household_Income": 25000,
}


@router.get("")
def list_scholarships(scholarship_type: Annotated[str, Query(alias="type")] = ""):
    scholarship_type = scholarship_type.strip()
    filters = {"type": scholarship_type} if scholarship_type else {}
    return catalog_service.list_entity("scholarships", filters)


@router.get("/{scholarship_id}")
def get_scholarship(scholarship_id: str):
    return {"data": catalog_service.get_entity("scholarships", scholarship_id.strip().upper())}


@router.post("", status_code=201)
def create_scholarship(payload: Annotated[dict, Body(examples=[SCHOLARSHIP_EXAMPLE])]):
    scholarship = catalog_service.create_entity("scholarships", payload)
    return {
        "message": f"Scholarship {scholarship['Scholarship_ID']} created successfully.",
        "data": scholarship,
    }


@router.put("/{scholarship_id}")
def update_scholarship(scholarship_id: str, payload: dict):
    """Update the supplied fields of a scholarship program."""
    scholarship = catalog_service.update_entity("scholarships", scholarship_id.strip().upper(), payload)
    return {
        "message": f"Scholarship {scholarship['Scholarship_ID']} updated successfully.",
        "data": scholarship,
    }


@router.delete("/{scholarship_id}")
def delete_scholarship(scholarship_id: str):
    return catalog_service.delete_entity("scholarships", scholarship_id.strip().upper())


@router.get("/{scholarship_id}/screening")
def screen_student(scholarship_id: str, student_id: str):
    """Compare a student's GPA and household income with the program's limits."""
    student_id = student_id.strip().upper()
    if not student_id:
        raise ValidationError(
            "Missing query parameter.",
            details={"fields": {"student_id": "Provide a student ID, e.g. S001."}},
        )
    result = eligibility_service.screen_student(scholarship_id.strip().upper(), student_id)
    return {"data": result}
