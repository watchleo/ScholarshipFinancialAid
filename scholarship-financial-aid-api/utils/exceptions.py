"""Custom exception hierarchy ([Unit II] Exceptions).

Every error the API raises is an ``AppError`` subclass, so the Flask error
handlers in ``api/__init__.py`` can convert it into a clean JSON response
with the right HTTP status code.
"""


class AppError(Exception):
    """Base class for all application errors."""

    status_code = 500
    code = "internal_error"

    def __init__(self, message, details=None):
        # Call the parent Exception constructor with the message
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self):
        """Render the error the way the API returns it (JSON-ready dict)."""
        error = {"code": self.code, "message": self.message}
        if self.details:
            error["details"] = self.details
        return {"error": error}


class BadRequestError(AppError):
    """The request itself is malformed (HTTP 400)."""

    status_code = 400
    code = "bad_request"


class NotFoundError(AppError):
    """The requested record does not exist (HTTP 404)."""

    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    """The request conflicts with existing data or state (HTTP 409)."""

    status_code = 409
    code = "conflict"


class ValidationError(AppError):
    """One or more fields failed validation (HTTP 422)."""

    status_code = 422
    code = "validation_failed"


class BusinessRuleError(AppError):
    """The data is valid but breaks an application rule (HTTP 422)."""

    status_code = 422
    code = "business_rule_violation"
