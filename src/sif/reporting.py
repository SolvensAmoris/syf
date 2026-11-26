"""Structured findings and logical status aggregation for SIF."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    severity: Severity
    outcome: Status | None = None
    context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not self.code:
            raise ValueError("finding code must be a non-empty string")
        if not isinstance(self.message, str) or not self.message:
            raise ValueError("finding message must be a non-empty string")
        if not isinstance(self.severity, Severity):
            raise TypeError("finding severity must be a Severity")
        if self.outcome is not None and not isinstance(self.outcome, Status):
            raise ValueError("finding outcome must be a Status or None")
        if self.outcome is Status.PASS:
            raise ValueError("finding outcome must be FAIL, UNKNOWN, or None")
        if not isinstance(self.context, dict):
            raise TypeError("finding context must be a dict")

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "outcome": self.outcome.value if self.outcome is not None else None,
            "context": dict(self.context),
        }

    def __getitem__(self, key: str) -> Any:
        """Temporary mapping-style compatibility for pre-B5 callers."""
        if key == "path":
            return self.context.get("path")
        if key in ("code", "message", "context"):
            return getattr(self, key)
        if key == "severity":
            return self.severity.value
        if key == "outcome":
            return self.outcome.value if self.outcome is not None else None
        raise KeyError(key)


def aggregate_status(findings: Iterable[Finding]) -> Status:
    """Aggregate logical outcomes; severity never determines the verdict."""
    has_unknown = False
    for finding in findings:
        if not isinstance(finding, Finding):
            raise TypeError("findings must contain only Finding instances")
        if finding.outcome is Status.FAIL:
            return Status.FAIL
        if finding.outcome is Status.UNKNOWN:
            has_unknown = True
    return Status.UNKNOWN if has_unknown else Status.PASS


class VerificationReport:
    """Structured verifier output; tuple access remains for legacy callers."""

    __slots__ = ("findings", "result")

    def __init__(
        self,
        status: Status | str | None = None,
        findings: Iterable[Finding] | None = None,
        result: Any = None,
    ) -> None:
        self.findings = list(findings or [])
        self.result = result
        computed = aggregate_status(self.findings)
        provided_status = status.value if isinstance(status, Status) else status
        if provided_status is not None and provided_status != computed.value:
            raise ValueError(
                f"provided status {status!r} conflicts with findings ({computed.value})"
            )

    @property
    def status(self) -> Status:
        return aggregate_status(self.findings)

    @property
    def has_warnings(self) -> bool:
        return any(f.severity is Severity.WARNING for f in self.findings)

    @property
    def has_info(self) -> bool:
        return any(f.severity is Severity.INFO for f in self.findings)

    @property
    def legacy_detail(self) -> Any:
        if self.status is Status.PASS:
            return self.result
        return self.findings[0].message if self.findings else None

    def add(self, finding: Finding) -> None:
        if not isinstance(finding, Finding):
            raise TypeError("report accepts only Finding instances")
        self.findings.append(finding)

    def extend(self, findings: Iterable[Finding]) -> None:
        additions = list(findings)
        if not all(isinstance(f, Finding) for f in additions):
            raise TypeError("report accepts only Finding instances")
        self.findings.extend(additions)

    def __getitem__(self, index: int) -> Any:
        if index == 0:
            return self.status
        if index == 1:
            return self.legacy_detail
        raise IndexError(index)

    def __iter__(self):
        yield self.status
        yield self.legacy_detail

    def __len__(self) -> int:
        return 2

    def as_dict(self) -> dict[str, Any]:
        report = {
            "status": self.status.value,
            "findings": [finding.as_dict() for finding in self.findings],
        }
        if self.result is not None:
            report["result"] = self.result
        return report

    def __eq__(self, other: object) -> bool:
        return isinstance(other, VerificationReport) and self.as_dict() == other.as_dict()

    def __repr__(self) -> str:
        return f"VerificationReport({self.as_dict()!r})"
