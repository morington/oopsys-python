import traceback
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Severity(str, Enum):
    ERROR = "error"
    CRITICAL = "critical"


class ErrorReport(BaseModel):
    severity: Severity
    service: str
    environment: str
    exception_type: str
    message: str
    traceback: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    context: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_exception(
        cls,
        exc: BaseException,
        *,
        severity: Severity,
        service: str,
        environment: str,
        context: dict[str, Any] | None = None,
    ) -> "ErrorReport":
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        return cls(
            severity=severity,
            service=service,
            environment=environment,
            exception_type=type(exc).__name__,
            message=str(exc) or type(exc).__name__,
            traceback=tb,
            context=context or {},
        )
