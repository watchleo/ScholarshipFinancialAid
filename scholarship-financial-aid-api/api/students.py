"""Student endpoints (REST resource: /api/students)."""

from flask import Blueprint, jsonify, request

from services import student_service
from api.common import get_json_body

students_bp = Blueprint("students", __name__)


@students_bp.get("/api/students")
def list_students():
    """GET - list students. Optional filters: ?search= &program= &year_level="""
    result = student_service.list_students(
        search=request.args.get("search", "").strip() or None,
        program=request.args.get("program", "").strip() or None,
        year_level=request.args.get("year_level", "").strip() or None,
    )
    return jsonify(result)


@students_bp.get("/api/students/<student_id>")
def get_student(student_id):
    """GET - fetch one student by ID."""
    return jsonify({"data": student_service.get_student(student_id.strip().upper())})


@students_bp.post("/api/students")
def create_student():
    """POST - register a new student (ID auto-generated when omitted)."""
    student = student_service.create_student(get_json_body())
    return jsonify({
        "message": f"Student {student['Student_ID']} created successfully.",
        "data": student,
    }), 201


@students_bp.put("/api/students/<student_id>")
def update_student(student_id):
    """PUT - partial update of one student."""
    student = student_service.update_student(
        student_id.strip().upper(), get_json_body())
    return jsonify({
        "message": f"Student {student['Student_ID']} updated successfully.",
        "data": student,
    })


@students_bp.delete("/api/students/<student_id>")
def delete_student(student_id):
    """DELETE - remove a student (409 while applications reference them)."""
    return jsonify(student_service.delete_student(student_id.strip().upper()))


@students_bp.get("/api/students/<student_id>/applications")
def list_student_applications(student_id):
    """GET - all applications of one student, plus a status summary."""
    return jsonify(
        student_service.get_student_applications(student_id.strip().upper()))
