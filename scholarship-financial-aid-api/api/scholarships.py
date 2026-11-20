"""Scholarship endpoints (REST resource: /api/scholarships)."""

from flask import Blueprint, jsonify, request

from services import catalog_service, eligibility_service
from utils.exceptions import ValidationError
from api.common import get_json_body

scholarships_bp = Blueprint("scholarships", __name__)


@scholarships_bp.get("/api/scholarships")
def list_scholarships():
    """GET - list scholarship programs. Optional filter: ?type=Merit-Based"""
    scholarship_type = request.args.get("type", "").strip() or None
    data = catalog_service.list_entity(
        "scholarships", {"type": scholarship_type} if scholarship_type else None)
    return jsonify(data)


@scholarships_bp.get("/api/scholarships/<scholarship_id>")
def get_scholarship(scholarship_id):
    """GET - fetch one scholarship program."""
    return jsonify({"data": catalog_service.get_entity(
        "scholarships", scholarship_id.strip().upper())})


@scholarships_bp.post("/api/scholarships")
def create_scholarship():
    """POST - create a scholarship program (ID auto-generated when omitted)."""
    scholarship = catalog_service.create_entity("scholarships", get_json_body())
    return jsonify({
        "message": f"Scholarship {scholarship['Scholarship_ID']} created "
                   f"successfully.",
        "data": scholarship,
    }), 201


@scholarships_bp.put("/api/scholarships/<scholarship_id>")
def update_scholarship(scholarship_id):
    """PUT - partial update of one scholarship program."""
    scholarship = catalog_service.update_entity(
        "scholarships", scholarship_id.strip().upper(), get_json_body())
    return jsonify({
        "message": f"Scholarship {scholarship_id.strip().upper()} updated "
                   f"successfully.",
        "data": scholarship,
    })


@scholarships_bp.delete("/api/scholarships/<scholarship_id>")
def delete_scholarship(scholarship_id):
    """DELETE - remove a scholarship (409 while applications reference it)."""
    return jsonify(catalog_service.delete_entity(
        "scholarships", scholarship_id.strip().upper()))


@scholarships_bp.get("/api/scholarships/<scholarship_id>/screening")
def screen_student(scholarship_id):
    """GET - eligibility screening of a student against a scholarship.

    Query parameter: ?student_id=S001
    (Rules are stored but NOT enforced - the result is informational.)
    """
    student_id = request.args.get("student_id", "").strip()
    if not student_id:
        raise ValidationError(
            "Missing query parameter.",
            details={"fields": {"student_id": "Query parameter 'student_id' "
                                              "is required (e.g. ?student_id=S001)."}})
    result = eligibility_service.screen_student(
        scholarship_id.strip().upper(), student_id.upper())
    return jsonify({"data": result})
