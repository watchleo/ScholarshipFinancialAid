"""Catalog endpoints for the five simple reference resources:

    /api/terms        /api/evaluators     /api/requirements
    /api/sponsors     /api/financial-aids

All five share the exact same CRUD shape, so the routes are registered in a
small loop instead of copy-pasting the same five handlers five times
([Unit II] loop + functions + dict/tuple data structures).
"""

from flask import Blueprint, jsonify, request

from services import base_service, catalog_service
from api.common import get_json_body

catalog_bp = Blueprint("catalog", __name__)

# (url prefix, service entity key, human label)
CATALOG_RESOURCES = (
    ("/api/terms", "terms", "Term"),
    ("/api/evaluators", "evaluators", "Evaluator"),
    ("/api/requirements", "requirements", "Requirement"),
    ("/api/sponsors", "sponsors", "Sponsor"),
    ("/api/financial-aids", "financial_aids", "Financial aid"),
)


def _register_resource(url_prefix, entity, label):
    """Register the five standard REST routes for one catalog resource."""

    id_field = base_service.TABLE_REGISTRY[entity]["id_field"]

    def list_items():
        # Only whitelisted filters (see catalog_service.FILTER_COLUMNS) apply
        filters = {
            key: value.strip()
            for key, value in request.args.items()
            if value.strip()
        }
        return jsonify(catalog_service.list_entity(entity, filters))

    def get_item(item_id):
        return jsonify({"data": catalog_service.get_entity(entity, item_id.upper())})

    def create_item():
        row = catalog_service.create_entity(entity, get_json_body())
        return jsonify({
            "message": f"{label} {row[id_field]} created successfully.",
            "data": row,
        }), 201

    def update_item(item_id):
        row = catalog_service.update_entity(entity, item_id.upper(), get_json_body())
        return jsonify({
            "message": f"{label} {item_id.upper()} updated successfully.",
            "data": row,
        })

    def delete_item(item_id):
        return jsonify(catalog_service.delete_entity(entity, item_id.upper()))

    catalog_bp.add_url_rule(url_prefix, f"list_{entity}", list_items, methods=["GET"])
    catalog_bp.add_url_rule(f"{url_prefix}/<item_id>", f"get_{entity}",
                            get_item, methods=["GET"])
    catalog_bp.add_url_rule(url_prefix, f"create_{entity}", create_item,
                            methods=["POST"])
    catalog_bp.add_url_rule(f"{url_prefix}/<item_id>", f"update_{entity}",
                            update_item, methods=["PUT"])
    catalog_bp.add_url_rule(f"{url_prefix}/<item_id>", f"delete_{entity}",
                            delete_item, methods=["DELETE"])


for _url_prefix, _entity, _label in CATALOG_RESOURCES:
    _register_resource(_url_prefix, _entity, _label)
