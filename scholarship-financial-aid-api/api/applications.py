"""Application endpoints - the main workflow of the system.

REST resources:
    /api/applications                                  (list / create)
    /api/applications/<id>                             (detail / update / delete)
    /api/applications/<id>/requirements                (checklist)
    /api/applications/<id>/requirements/<req_id>       (remove one entry)
    /api/applications/<id>/review                      (approve / reject)
    /api/applications/<id>/renew                       (renewal application)
    /api/applications/<id>/screening                   (eligibility report)
    /api/applications/<id>/disbursements               (installments)
    /api/disbursements                                 (global list)
"""

from flask import Blueprint, jsonify, request

from services import application_service, disbursement_service
from api.common import get_json_body

applications_bp = Blueprint("applications", __name__)


@applications_bp.get("/api/applications")
def list_applications():
    """GET - list applications.

    Optional filters:
      ?status=Approved  &student_id=S001  &term_id=T01
      &scholarship_id=SCH01 (or 'none')   &evaluator_id=E01
      &aid_id=FA01      &previous_application_id=A001
    """
    result = application_service.list_applications(
        status=request.args.get("status"),
        student_id=request.args.get("student_id"),
        scholarship_id=request.args.get("scholarship_id"),
        aid_id=request.args.get("aid_id"),
        term_id=request.args.get("term_id"),
        evaluator_id=request.args.get("evaluator_id"),
        previous_application_id=request.args.get("previous_application_id"),
    )
    return jsonify(result)


@applications_bp.post("/api/applications")
def create_application():
    """POST - submit a new application (always starts as Pending)."""
    detail = application_service.create_application(get_json_body())
    return jsonify({
        "message": (f"Application {detail['Application_ID']} submitted "
                    f"successfully (status: Pending)."),
        "data": detail,
    }), 201


@applications_bp.get("/api/applications/<application_id>")
def get_application(application_id):
    """GET - one application with joined names, totals and screening."""
    return jsonify({"data": application_service.get_application(
        application_id.strip().upper())})


@applications_bp.put("/api/applications/<application_id>")
def update_application(application_id):
    """PUT - partial update (Status/Award_Amount only via /review)."""
    detail = application_service.update_application(
        application_id.strip().upper(), get_json_body())
    return jsonify({
        "message": f"Application {detail['Application_ID']} updated successfully.",
        "data": detail,
    })


@applications_bp.delete("/api/applications/<application_id>")
def delete_application(application_id):
    """DELETE - remove an application (checklist + disbursements cascade)."""
    return jsonify(application_service.delete_application(
        application_id.strip().upper()))


@applications_bp.get("/api/applications/<application_id>/requirements")
def list_requirements(application_id):
    """GET - the requirement checklist of one application."""
    return jsonify(application_service.list_requirements(
        application_id.strip().upper()))


@applications_bp.post("/api/applications/<application_id>/requirements")
def attach_requirement(application_id):
    """POST - attach (or update) a requirement in the checklist.

    Body: {"Requirement_ID": "R01",
           "Requirement_Status": "Verified",
           "Submitted_Date": "2026-06-14"}
    """
    return jsonify(application_service.attach_requirement(
        application_id.strip().upper(), get_json_body()))


@applications_bp.delete(
    "/api/applications/<application_id>/requirements/<requirement_id>")
def remove_requirement(application_id, requirement_id):
    """DELETE - remove one requirement from the checklist."""
    return jsonify(application_service.remove_requirement(
        application_id.strip().upper(), requirement_id.strip().upper()))


@applications_bp.post("/api/applications/<application_id>/review")
def review_application(application_id):
    """POST - evaluator decision.

    Body: {"action": "approve", "award_amount": 25000}
       or {"action": "reject"}
    """
    return jsonify(application_service.review_application(
        application_id.strip().upper(), get_json_body()))


@applications_bp.post("/api/applications/<application_id>/renew")
def renew_application(application_id):
    """POST - create a renewal for a different term, linked to this one.

    Body: {"Term_ID": "T03", "Evaluator_ID": "E01"}   (Evaluator optional)
    """
    result = application_service.renew_application(
        application_id.strip().upper(), get_json_body())
    return jsonify(result), 201


@applications_bp.get("/api/applications/<application_id>/screening")
def screen_application(application_id):
    """GET - eligibility screening of the application's student."""
    from services import eligibility_service
    return jsonify({"data": eligibility_service.screen_application(
        application_id.strip().upper())})


@applications_bp.get("/api/applications/<application_id>/disbursements")
def list_application_disbursements(application_id):
    """GET - disbursements of one application."""
    return jsonify(disbursement_service.list_disbursements(
        application_id=application_id.strip().upper()))


@applications_bp.post("/api/applications/<application_id>/disbursements")
def create_disbursement(application_id):
    """POST - record a disbursement installment (application must be Approved).

    Body: {"Disbursement_Date": "2026-07-15",
           "Disbursement_Amount": 12500,
           "Payment_Method": "Bank Transfer",
           "Payment_Reference_No": "REF-2026-0715-006",
           "Disbursement_Note": "1st installment"}
    """
    return jsonify(disbursement_service.create_disbursement(
        application_id.strip().upper(), get_json_body())), 201


@applications_bp.get("/api/disbursements")
def list_disbursements():
    """GET - all disbursements. Optional: ?application_id=A001 &payment_method=GCash"""
    return jsonify(disbursement_service.list_disbursements(
        application_id=request.args.get("application_id"),
        payment_method=request.args.get("payment_method"),
    ))


@applications_bp.get("/api/disbursements/<disbursement_id>")
def get_disbursement(disbursement_id):
    """GET - fetch one disbursement by ID."""
    return jsonify({"data": disbursement_service.get_disbursement(
        disbursement_id.strip().upper())})


@applications_bp.delete("/api/disbursements/<disbursement_id>")
def delete_disbursement(disbursement_id):
    """DELETE - remove a disbursement (e.g. to correct a mistake)."""
    return jsonify(disbursement_service.delete_disbursement(
        disbursement_id.strip().upper()))
