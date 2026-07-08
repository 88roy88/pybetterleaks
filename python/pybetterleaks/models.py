from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Optional


def _optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _optional_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _str_dict(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): str(item) for key, item in value.items() if item is not None}


def _any_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None]


@dataclass(frozen=True)
class ScanError:
    """Structured error returned by the native bridge."""

    code: str
    """Stable machine-readable error code."""

    message: str
    """Human-readable error summary."""

    detail: Optional[str] = None
    """Optional native error detail."""

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ScanError":
        return cls(
            code=str(value.get("code") or "native_error"),
            message=str(value.get("message") or "Betterleaks scan failed"),
            detail=_optional_str(value.get("detail")),
        )


@dataclass(frozen=True)
class Finding:
    """Secret finding returned by Betterleaks."""

    rule_id: str
    """Betterleaks rule identifier."""

    description: Optional[str] = None
    """Rule description, when provided by Betterleaks."""

    file: Optional[str] = None
    """File path for directory scans, if available."""

    line: Optional[int] = None
    """One-based start line, if available."""

    column: Optional[int] = None
    """One-based start column, if available."""

    end_line: Optional[int] = None
    """One-based end line, if available."""

    end_column: Optional[int] = None
    """One-based end column, if available."""

    secret: Optional[str] = None
    """Secret value, usually `REDACTED` unless redaction is disabled."""

    match: Optional[str] = None
    """Matched text around the secret, when Betterleaks provides it."""

    validation_status: Optional[str] = None
    """Validation status reported by Betterleaks."""

    validation_meta: dict[str, Any] = field(default_factory=dict)
    """Additional validation metadata."""

    tags: list[str] = field(default_factory=list)
    """Rule tags."""

    attributes: dict[str, str] = field(default_factory=dict)
    """Additional normalized attributes such as fingerprint and entropy."""

    raw: dict[str, Any] = field(default_factory=dict)
    """Forward-compatible raw Betterleaks fields."""

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Finding":
        return cls(
            rule_id=str(value.get("rule_id") or value.get("ruleID") or value.get("RuleID") or ""),
            description=_optional_str(value.get("description") or value.get("Description")),
            file=_optional_str(value.get("file") or value.get("File")),
            line=_optional_int(value.get("line") or value.get("Line") or value.get("start_line")),
            column=_optional_int(
                value.get("column") or value.get("Column") or value.get("start_column")
            ),
            end_line=_optional_int(value.get("end_line") or value.get("EndLine")),
            end_column=_optional_int(value.get("end_column") or value.get("EndColumn")),
            secret=_optional_str(value.get("secret") or value.get("Secret")),
            match=_optional_str(value.get("match") or value.get("Match")),
            validation_status=_optional_str(
                value.get("validation_status") or value.get("ValidationStatus")
            ),
            validation_meta=_any_dict(value.get("validation_meta") or value.get("ValidationMeta")),
            tags=_str_list(value.get("tags") or value.get("Tags")),
            attributes=_str_dict(value.get("attributes") or value.get("Attributes")),
            raw=_any_dict(value),
        )


@dataclass(frozen=True)
class ScanResult:
    """Result returned by `scan_text` and `scan_dir`."""

    findings: list[Finding]
    """Findings produced by the scan."""

    errors: list[ScanError]
    """Structured native errors. Empty means the scan succeeded."""

    betterleaks_version: str
    """Betterleaks version bundled into the native bridge."""

    @property
    def ok(self) -> bool:
        """Whether the scan completed without structured native errors."""
        return not self.errors

    @classmethod
    def from_native_response(cls, response: Mapping[str, Any]) -> "ScanResult":
        findings_value = response.get("findings")
        errors_value = response.get("errors")

        findings: list[Finding] = []
        if isinstance(findings_value, list):
            findings = [
                Finding.from_mapping(item) for item in findings_value if isinstance(item, Mapping)
            ]

        errors: list[ScanError] = []
        if isinstance(errors_value, list):
            errors = [
                ScanError.from_mapping(item) for item in errors_value if isinstance(item, Mapping)
            ]

        if response.get("ok") is False and not errors:
            errors.append(
                ScanError(
                    code="native_error",
                    message="Betterleaks native bridge reported failure",
                    detail=None,
                )
            )

        return cls(
            findings=findings,
            errors=errors,
            betterleaks_version=str(response.get("betterleaks_version") or ""),
        )
