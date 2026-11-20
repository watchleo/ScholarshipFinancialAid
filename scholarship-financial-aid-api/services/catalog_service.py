"""CRUD for the simple reference ("catalog") entities:

terms, evaluators, requirements, sponsors, financial aids.

All five tables share the same simple shape, so one module with a shared
validator map handles them all.
"""

from database import db
from services import base_service
from utils import validators
from utils.app_logger import get_logger
from utils.exceptions import ConflictError, ValidationError

logger = get_logger("catalog")

# entity key -> its validator function (see utils/validators.py)
ENTITY_VALIDATORS = {
    "terms": validators.validate_term,
    "evaluators": validators.validate_evaluator,
    "requirements": validators.validate_requirement,
    "sponsors": validators.validate_sponsor,
    "financial_aids": validators.validate_financial_aid,
}

# Allowed ?query filters per entity: query param -> physical column
FILTER_COLUMNS = {
    "scholarships": {"type": "Scholarship_Type"},
    "terms": {"academic_year": "Academic_Year"},
    "sponsors": {"sponsor_type": "Sponsor_Type"},
    "financial_aids": {"sponsor_id": "Sponsor_ID"},
}


def list_entity(entity, filters=None):
    """List rows with optional whitelisted filters (e.g. ?sponsor_id=SP01)."""
    filters = filters or {}
    conditions, params = [], []

    for param, column in FILTER_COLUMNS.get(entity, {}).items():
        value = filters.get(param)
        if value:                                    # skip empty filters
            conditions.append(f"{column} = ?")
            params.append(value.strip().upper() if param.endswith("_id") else value.strip())

    where = " AND ".join(conditions) if conditions else None
    data = base_service.list_rows(entity, where=where, params=params)
    return {"count": len(data), "filters": filters, "data": data}


def get_entity(entity, item_id):
    return base_service.get_row(entity, item_id)


def create_entity(entity, payload):
    """Validate + insert one catalog row; auto-generates the ID if missing."""
    validator = ENTITY_VALIDATORS[entity]
    cleaned = validator(payload)                    # raises ValidationError (422)
    registry = base_service.TABLE_REGISTRY[entity]
    id_field = registry["id_field"]

    # Auto-generate the primary key when the client did not send one
    if id_field not in cleaned:
        cleaned[id_field] = base_service.generate_id(entity)
    elif base_service.row_exists(entity, cleaned[id_field]):
        raise ConflictError(
            f"{registry['label']} '{cleaned[id_field]}' already exists."
        )

    # Foreign key existence check (only financial aids have one: sponsor)
    _ensure_references(entity, cleaned)

    row = base_service.insert_row(entity, cleaned)
    logger.info("Created %s %s", entity, row[id_field])
    return row


def update_entity(entity, item_id, payload):
    """Partial update of one catalog row (only sent fields are changed)."""
    current = base_service.get_row(entity, item_id)     # 404 when missing
    registry = base_service.TABLE_REGISTRY[entity]
    id_field = registry["id_field"]

    if id_field in payload and payload[id_field] != item_id:
        raise ValidationError(
            "Primary keys cannot be changed.",
            details={"fields": {id_field: f"Must stay '{item_id}'."}},
        )

    cleaned = ENTITY_VALIDATORS[entity](payload, partial=True)
    _ensure_references(entity, cleaned)

    row = base_service.update_row(entity, item_id, cleaned)
    logger.info("Updated %s %s", entity, item_id)
    return row


def delete_entity(entity, item_id):
    result = base_service.delete_row(entity, item_id)
    logger.info("Deleted %s %s", entity, item_id)
    return result


def _ensure_references(entity, cleaned):
    """Check that referenced rows exist (used by financial aids -> sponsors)."""
    if entity == "financial_aids" and "Sponsor_ID" in cleaned:
        sponsor_id = cleaned["Sponsor_ID"]
        if not base_service.row_exists("sponsors", sponsor_id):
            raise ValidationError(
                "Financial aid references an unknown sponsor.",
                details={"fields": {"Sponsor_ID": f"Sponsor '{sponsor_id}' does not exist."}},
            )
