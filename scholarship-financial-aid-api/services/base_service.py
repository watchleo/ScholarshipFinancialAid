"""Generic CRUD helpers shared by all entity services.

TABLE_REGISTRY maps each API entity key to its physical table plus the
columns used for ordering and automatic ID generation. All SQL identifiers
come from this trusted registry (never from user input), and all values
are passed as ``?`` parameters, so SQL injection is not possible.

[Unit II] Built-in Data Structures: the registry is a dict of dicts, and
query results are converted to lists of dicts with a list comprehension.
"""

import sqlite3

from database import db
from utils.exceptions import ConflictError, NotFoundError
from utils.formatters import next_sequential_id

TABLE_REGISTRY = {
    "students": {"table": "Students", "id_field": "Student_ID", "prefix": "S",
                 "label": "Student", "order_by": "Student_Name"},
    "scholarships": {"table": "Scholarship", "id_field": "Scholarship_ID", "prefix": "SCH",
                     "label": "Scholarship", "order_by": "Scholarship_ID"},
    "terms": {"table": "Academic_Terms", "id_field": "Term_ID", "prefix": "T",
              "label": "Term", "order_by": "Term_ID"},
    "evaluators": {"table": "Evaluators", "id_field": "Evaluator_ID", "prefix": "E",
                   "label": "Evaluator", "order_by": "Evaluator_ID"},
    "requirements": {"table": "Requirements", "id_field": "Requirement_ID", "prefix": "R",
                     "label": "Requirement", "order_by": "Requirement_ID"},
    "sponsors": {"table": "Sponsors", "id_field": "Sponsor_ID", "prefix": "SP",
                 "label": "Sponsor", "order_by": "Sponsor_ID"},
    "financial_aids": {"table": "Financial_Aid", "id_field": "Aid_ID", "prefix": "FA",
                       "label": "Financial aid", "order_by": "Aid_ID"},
    "applications": {"table": "Applications", "id_field": "Application_ID", "prefix": "A",
                     "label": "Application", "order_by": "Application_Date, Application_ID"},
    "disbursements": {"table": "Disbursements", "id_field": "Disbursement_ID", "prefix": "D",
                      "label": "Disbursement", "order_by": "Disbursement_Date, Disbursement_ID"},
    # Export-only: composite PK, so it has no auto-generated single ID
    "application_requirements": {"table": "Application_Requirements",
                                 "id_field": "Application_ID", "prefix": "",
                                 "label": "Requirement entry",
                                 "order_by": "Application_ID, Requirement_ID"},
}


def list_rows(entity, where=None, params=None):
    """Return every row of an entity (optionally filtered) as dicts."""
    registry = TABLE_REGISTRY[entity]
    sql = f"SELECT * FROM {registry['table']}"
    if where:
        sql += f" WHERE {where}"
    sql += f" ORDER BY {registry['order_by']}"

    with db.get_db() as conn:
        rows = conn.execute(sql, params or []).fetchall()
    return [dict(row) for row in rows]      # list comprehension -> list of dicts


def get_row(entity, row_id):
    """Fetch one row by primary key; raises NotFoundError (HTTP 404)."""
    registry = TABLE_REGISTRY[entity]
    sql = f"SELECT * FROM {registry['table']} WHERE {registry['id_field']} = ?"
    with db.get_db() as conn:
        row = conn.execute(sql, [row_id]).fetchone()
    if row is None:
        raise NotFoundError(f"{registry['label']} '{row_id}' not found.")
    return dict(row)


def row_exists(entity, row_id):
    """True when a row with this primary key exists."""
    registry = TABLE_REGISTRY[entity]
    sql = f"SELECT 1 FROM {registry['table']} WHERE {registry['id_field']} = ?"
    with db.get_db() as conn:
        return conn.execute(sql, [row_id]).fetchone() is not None


def existing_ids(entity):
    """All primary key values of an entity (used for ID auto-generation)."""
    registry = TABLE_REGISTRY[entity]
    sql = f"SELECT {registry['id_field']} AS id FROM {registry['table']}"
    with db.get_db() as conn:
        rows = conn.execute(sql).fetchall()
    return [row["id"] for row in rows]


def generate_id(entity):
    """Next free ID for an entity, e.g. 'A007' for applications."""
    registry = TABLE_REGISTRY[entity]
    return next_sequential_id(existing_ids(entity), registry["prefix"])


def insert_row(entity, values):
    """Insert one row (values = validated dict) and return the stored row."""
    registry = TABLE_REGISTRY[entity]
    columns = ", ".join(values.keys())
    placeholders = ", ".join("?" * len(values))
    sql = f"INSERT INTO {registry['table']} ({columns}) VALUES ({placeholders})"

    try:
        with db.get_db() as conn:
            conn.execute(sql, list(values.values()))
    except sqlite3.IntegrityError as error:
        # e.g. duplicate primary key or UNIQUE email
        raise ConflictError(
            f"Could not save the {registry['label'].lower()}: {error}"
        ) from error
    return get_row(entity, values[registry["id_field"]])


def update_row(entity, row_id, values):
    """Update the given columns of one row; returns the updated row."""
    registry = TABLE_REGISTRY[entity]
    if not values:
        return get_row(entity, row_id)     # nothing to change

    # "ColumnA = ?, ColumnB = ?" built from VALIDATED field names only
    assignments = ", ".join(f"{column} = ?" for column in values.keys())
    sql = (f"UPDATE {registry['table']} SET {assignments} "
           f"WHERE {registry['id_field']} = ?")
    try:
        with db.get_db() as conn:
            conn.execute(sql, [*values.values(), row_id])
    except sqlite3.IntegrityError as error:
        raise ConflictError(
            f"Could not update {registry['label'].lower()} '{row_id}': {error}"
        ) from error
    return get_row(entity, row_id)


def delete_row(entity, row_id):
    """Delete one row. Referenced rows block deletion (409, FK constraint)."""
    registry = TABLE_REGISTRY[entity]

    get_row(entity, row_id)                # clean 404 when it doesn't exist

    sql = f"DELETE FROM {registry['table']} WHERE {registry['id_field']} = ?"
    try:
        with db.get_db() as conn:
            conn.execute(sql, [row_id])
    except sqlite3.IntegrityError:
        # [Case study] FK integrity: e.g. a student with applications, or a
        # sponsor that still funds financial aid programs, cannot be deleted.
        raise ConflictError(
            f"Cannot delete {registry['label'].lower()} '{row_id}' because "
            f"other records still reference it (foreign key constraint)."
        )
    return {"message": f"{registry['label']} '{row_id}' deleted successfully."}
