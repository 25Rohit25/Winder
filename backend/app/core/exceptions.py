"""Domain exceptions for WindCtrl Validate."""

from typing import Any, Dict, Optional


class WindCtrlException(Exception):
    """Base exception for all WindCtrl Validate domain errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SignalIntegrityError(WindCtrlException):
    """Raised when incoming telemetry fails basic integrity checks."""


class DatasetNotFoundError(WindCtrlException):
    """Raised when a requested dataset file or identifier cannot be resolved."""


class ValidationExecutionError(WindCtrlException):
    """Raised when an internal error occurs during validation rule execution."""


class FaultInjectionError(WindCtrlException):
    """Raised when a synthetic fault scenario configuration is invalid."""


class ReportGenerationError(WindCtrlException):
    """Raised when compilation or rendering of engineering reports fails."""


class InvalidTelemetryError(WindCtrlException):
    """Raised when telemetry column schemas or data types violate specifications."""
