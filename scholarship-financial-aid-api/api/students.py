"""HTTP endpoints for student records and their applications."""

from typing import Annotated

from fastapi import APIRouter, Body

from services import student_service

router = APIRouter(prefix="/api/students", tags=["Students"])

STUDENT_EXAMPLE = {
    "Student_Name": "Alex Cruz",
    "Program": "BS Education",
    "Year_Level": "1st Year",
    "Email": "alex.cruz@example.org",
    "Contact_No": "0917-555-0142",
    "Household_Income": 14000,
    "GPA": 1.75,
}


@router.get("")
def list_students(search: str = "", program: str = "", year_level: str = ""):
    """Find students by name or email, program, and year level."""
    return student_service.list_students(
        search=search.strip() or None,
        program=program.strip() or None,
        year_level=year_level.strip() or None,
    )


@router.get("/{student_id}")
def get_student(student_id: str):
    return {"data": student_service.get_student(student_id.strip().upper())}


@router.post("", status_code=201)
def create_student(payload: Annotated[dict, Body(examples=[STUDENT_EXAMPLE])]):
    """Register a student and assign an ID when one is omitted."""
    student = student_service.create_student(payload)
    return {
        "message": f"Student {student['Student_ID']} created successfully.",
        "data": student,
    }


@router.put("/{student_id}")
def update_student(student_id: str, payload: dict):
    """Update the supplied fields of a student record."""
    student = student_service.update_student(student_id.strip().upper(), payload)
    return {
        "message": f"Student {student['Student_ID']} updated successfully.",
        "data": student,
    }


@router.delete("/{student_id}")
def delete_student(student_id: str):
    return student_service.delete_student(student_id.strip().upper())


@router.get("/{student_id}/applications")
def list_student_applications(student_id: str):
    return student_service.get_student_applications(student_id.strip().upper())
