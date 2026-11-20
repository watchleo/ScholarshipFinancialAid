"""REST routes for the five reference tables used in applications."""

from typing import Annotated

from fastapi import APIRouter, Body, Request

from services import base_service, catalog_service

router = APIRouter(tags=["Catalog"])


def register_resource(path, entity, label, example):
    """Bind standard collection and item routes to one catalog service entity."""
    id_field = base_service.TABLE_REGISTRY[entity]["id_field"]
    item_path = path + "/{item_id}"
    query_fields = [
        {"in": "query", "name": name, "schema": {"type": "string"}, "required": False}
        for name in catalog_service.FILTER_COLUMNS.get(entity, {})
    ]

    @router.get(path, name=f"list_{entity}", openapi_extra={"parameters": query_fields})
    def list_items(request: Request):
        filters = {
            key: value.strip()
            for key, value in request.query_params.items()
            if value.strip()
        }
        return catalog_service.list_entity(entity, filters)

    @router.get(item_path, name=f"get_{entity}")
    def get_item(item_id: str):
        return {"data": catalog_service.get_entity(entity, item_id.strip().upper())}

    @router.post(path, name=f"create_{entity}", status_code=201)
    def create_item(payload: Annotated[dict, Body(examples=[example])]):
        row = catalog_service.create_entity(entity, payload)
        return {"message": f"{label} {row[id_field]} created successfully.", "data": row}

    @router.put(item_path, name=f"update_{entity}")
    def update_item(item_id: str, payload: dict):
        row = catalog_service.update_entity(entity, item_id.strip().upper(), payload)
        return {"message": f"{label} {row[id_field]} updated successfully.", "data": row}

    @router.delete(item_path, name=f"delete_{entity}")
    def delete_item(item_id: str):
        return catalog_service.delete_entity(entity, item_id.strip().upper())


register_resource("/api/terms", "terms", "Term", {
    "Term_Name": "2nd Semester", "Academic_Year": "2026-2027",
})
register_resource("/api/evaluators", "evaluators", "Evaluator", {
    "Evaluator_Name": "Prof. Dani Ruiz",
})
register_resource("/api/requirements", "requirements", "Requirement", {
    "Requirement_Name": "Personal Statement",
})
register_resource("/api/sponsors", "sponsors", "Sponsor", {
    "Sponsor_Name": "Community Partners",
    "Sponsor_Type": "Foundation",
    "Sponsor_Email": "aid@example.org",
    "Sponsor_Contact_No": "0917-555-0151",
    "Sponsor_Budget": 100000,
})
register_resource("/api/financial-aids", "financial_aids", "Financial aid", {
    "Sponsor_ID": "SP01", "Aid_Type": "Books", "Aid_Description": "Book allowance",
})
