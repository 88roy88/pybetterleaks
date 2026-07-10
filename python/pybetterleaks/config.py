from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from .exceptions import ConfigFormatError

PathInput = Union[str, os.PathLike[str]]


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _toml_bool(value: bool) -> str:
    return "true" if value else "false"


def _toml_string_list(values: list[str]) -> str:
    return "[" + ", ".join(_toml_string(value) for value in values) + "]"


@dataclass(frozen=True)
class Expr:
    """Betterleaks Expr expression used in filters and validation."""

    value: str
    """Raw Expr source."""

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ConfigFormatError("Expr value cannot be empty")

    def __str__(self) -> str:
        return self.value

    @staticmethod
    def finding(field: str = "secret") -> str:
        """Return a Betterleaks Expr reference such as `finding["secret"]`."""
        _ensure_non_empty("finding field", field)
        return f"finding[{_toml_string(field)}]"

    @staticmethod
    def attribute(name: str = "path", *, default: str = "") -> str:
        """Return a Betterleaks Expr attribute lookup with a default value."""
        _ensure_non_empty("attribute name", name)
        return f"get(attributes, {_toml_string(name)}, {_toml_string(default)})"

    @classmethod
    def min_entropy(cls, threshold: float, *, field: str = "secret") -> "Expr":
        """Build a rule filter that keeps only findings above an entropy threshold.

        Betterleaks filter expressions return `True` when a finding should be
        skipped, so this helper emits a "skip when entropy is too low" predicate.
        """
        if threshold <= 0:
            raise ConfigFormatError("entropy threshold must be greater than zero")
        if not field.strip():
            raise ConfigFormatError("entropy field cannot be empty")
        return cls(
            f"filter.entropy({cls.finding(field)}) <= {_toml_float(threshold)}"
        )

    @classmethod
    def token_efficiency(cls, *, field: str = "secret") -> "Expr":
        """Build a filter predicate that skips token-efficient natural text."""
        return cls(f"filter.failsTokenEfficiency({cls.finding(field)})")

    @classmethod
    def finding_contains_any(cls, values: Sequence[str], *, field: str = "secret") -> "Expr":
        """Build `filter.containsAny(finding[field], values)`."""
        return cls(f"filter.containsAny({cls.finding(field)}, {_expr_string_list(values)})")

    @classmethod
    def finding_matches_any(cls, patterns: Sequence[str], *, field: str = "secret") -> "Expr":
        """Build `filter.matchesAny(finding[field], regex_patterns)`."""
        return cls(f"filter.matchesAny({cls.finding(field)}, {_expr_regex_list(patterns)})")

    @classmethod
    def attribute_contains_any(
        cls,
        name: str,
        values: Sequence[str],
        *,
        default: str = "",
    ) -> "Expr":
        """Build `filter.containsAny(get(attributes, name, default), values)`."""
        return cls(
            "filter.containsAny("
            f"{cls.attribute(name, default=default)}, {_expr_string_list(values)}"
            ")"
        )

    @classmethod
    def attribute_matches_any(
        cls,
        name: str,
        patterns: Sequence[str],
        *,
        default: str = "",
    ) -> "Expr":
        """Build `filter.matchesAny(get(attributes, name, default), regex_patterns)`."""
        return cls(
            "filter.matchesAny("
            f"{cls.attribute(name, default=default)}, {_expr_regex_list(patterns)}"
            ")"
        )

    @classmethod
    def path_matches_any(cls, patterns: Sequence[str]) -> "Expr":
        """Build the modern equivalent of a path allowlist predicate."""
        return cls.attribute_matches_any("path", patterns)

    @classmethod
    def git_commit_in(cls, commits: Sequence[str]) -> "Expr":
        """Build the modern equivalent of a commit allowlist predicate."""
        return cls(f'{cls.attribute("git.sha")} in {_expr_string_list(commits)}')

    @classmethod
    def any_of(cls, *expressions: ExprInput) -> "Expr":
        """Combine expressions with `||`."""
        parts = _expr_parts(expressions)
        return cls(" || ".join(f"({part})" for part in parts))

    @classmethod
    def all_of(cls, *expressions: ExprInput) -> "Expr":
        """Combine expressions with `&&`."""
        parts = _expr_parts(expressions)
        return cls(" && ".join(f"({part})" for part in parts))

    @classmethod
    def not_(cls, expression: ExprInput) -> "Expr":
        """Negate an expression."""
        return cls(f"!({_expr_part(expression)})")


class Validation:
    """Helpers for Betterleaks rule `validate` expressions."""

    @staticmethod
    def result(status: str, **metadata: str) -> Expr:
        """Build a structured validation result object expression."""
        _ensure_non_empty("validation status", status)
        if "result" in metadata:
            raise ConfigFormatError("validation metadata cannot override result")
        return Expr(_expr_object({"result": status, **metadata}))

    @classmethod
    def valid(cls, **metadata: str) -> Expr:
        """Build `{"result": "valid"}` with optional metadata."""
        return cls.result("valid", **metadata)

    @classmethod
    def invalid(cls, *, reason: Optional[str] = None, **metadata: str) -> Expr:
        """Build `{"result": "invalid"}` with an optional reason."""
        if reason is not None:
            metadata = {"reason": reason, **metadata}
        return cls.result("invalid", **metadata)

    @classmethod
    def unknown(cls, response_expr: Optional[str] = None, **metadata: str) -> Expr:
        """Build an unknown validation result or `validate.unknown(response)` call."""
        if response_expr is not None:
            if metadata:
                raise ConfigFormatError("metadata cannot be combined with response_expr")
            _ensure_non_empty("response expression", response_expr)
            return Expr(f"validate.unknown({response_expr})")
        return cls.result("unknown", **metadata)

    @classmethod
    def needs_validation(cls, **metadata: str) -> Expr:
        """Build `{"result": "needs_validation"}` with optional metadata."""
        return cls.result("needs_validation", **metadata)

    @staticmethod
    def bearer_get(
        url: str,
        success_check: str,
        *,
        token_field: str = "secret",
        valid_status: int = 200,
        invalid_statuses: Sequence[int] = (401, 403),
        invalid_reason: str = "Unauthorized",
        accept_json: bool = True,
    ) -> Expr:
        """Build a common HTTP bearer-token validation expression."""
        _ensure_non_empty("validation URL", url)
        _ensure_non_empty("success check", success_check)
        _ensure_positive_status("valid_status", valid_status)
        statuses = _status_list(invalid_statuses)

        headers = [
            f'{_toml_string("Authorization")}: "Bearer " + {Expr.finding(token_field)}',
        ]
        if accept_json:
            headers.append(f'{_toml_string("Accept")}: "application/json"')

        return Expr(
            "let r = http.get("
            + _toml_string(url)
            + ", {\n    "
            + ",\n    ".join(headers)
            + "\n  });\n"
            + f"r.status == {valid_status} && ({success_check}) ? "
            + str(Validation.valid())
            + f" : r.status in {_expr_int_list(statuses)} ? "
            + str(Validation.invalid(reason=invalid_reason))
            + " : validate.unknown(r)"
        )


ExprInput = Union[str, Expr]


def _expr_value(value: Optional[ExprInput]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, Expr):
        return value.value
    return str(value)


def _expr_part(value: ExprInput) -> str:
    part = _expr_value(value)
    if part is None or not part.strip():
        raise ConfigFormatError("expression cannot be empty")
    return part


def _expr_parts(values: Sequence[ExprInput]) -> list[str]:
    if not values:
        raise ConfigFormatError("at least one expression is required")
    return [_expr_part(value) for value in values]


def _toml_float(value: float) -> str:
    raw = f"{value:g}"
    if "." not in raw and "e" not in raw:
        raw += ".0"
    return raw


def _ensure_non_empty(name: str, value: str) -> None:
    if not value.strip():
        raise ConfigFormatError(f"{name} cannot be empty")


def _ensure_values(name: str, values: Sequence[str]) -> list[str]:
    items = list(values)
    if not items:
        raise ConfigFormatError(f"{name} cannot be empty")
    for item in items:
        if not item.strip():
            raise ConfigFormatError(f"{name} cannot contain empty values")
    return items


def _expr_regex(value: str) -> str:
    _ensure_non_empty("regex pattern", value)
    if "`" not in value:
        return f"`{value}`"
    return _toml_string(value)


def _expr_regex_list(values: Sequence[str]) -> str:
    patterns = ", ".join(
        _expr_regex(value) for value in _ensure_values("regex list", values)
    )
    return f"[{patterns}]"


def _expr_string_list(values: Sequence[str]) -> str:
    return _toml_string_list(_ensure_values("string list", values))


def _expr_int_list(values: Sequence[int]) -> str:
    return "[" + ", ".join(str(value) for value in values) + "]"


def _expr_object(values: Mapping[str, str]) -> str:
    return json.dumps(values, ensure_ascii=False, separators=(",", ":"))


def _ensure_positive_status(name: str, status: int) -> None:
    if status <= 0:
        raise ConfigFormatError(f"{name} must be greater than zero")


def _status_list(statuses: Sequence[int]) -> list[int]:
    values = list(statuses)
    if not values:
        raise ConfigFormatError("invalid_statuses cannot be empty")
    for status in values:
        _ensure_positive_status("invalid status", status)
    return values


@dataclass(frozen=True)
class Extend:
    """Betterleaks `[extend]` configuration."""

    path: Optional[PathInput] = None
    url: Optional[str] = None
    use_default: bool = False
    disabled_rules: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.path is not None and self.use_default:
            raise ConfigFormatError("extend.path and extend.use_default cannot both be set")
        if self.path is not None and self.url is not None:
            raise ConfigFormatError("extend.path and extend.url cannot both be set")

    def _is_empty(self) -> bool:
        return (
            self.path is None
            and self.url is None
            and not self.use_default
            and not self.disabled_rules
        )

    def _toml_lines(self, *, base_path: Optional[PathInput] = None) -> list[str]:
        lines = ["[extend]"]
        if self.path is not None:
            lines.append(f"path = {_toml_string(_resolve_extend_path(self.path, base_path))}")
        if self.url is not None:
            lines.append(f"url = {_toml_string(self.url)}")
        if self.use_default:
            lines.append(f"useDefault = {_toml_bool(self.use_default)}")
        if self.disabled_rules:
            lines.append(f"disabledRules = {_toml_string_list(self.disabled_rules)}")
        return lines


@dataclass(frozen=True)
class RequiredRule:
    """Composite rule dependency in `[[rules.required]]`."""

    id: str
    within_lines: Optional[int] = None
    within_columns: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ConfigFormatError("required rule id cannot be empty")
        for name, value in (
            ("within_lines", self.within_lines),
            ("within_columns", self.within_columns),
        ):
            if value is not None and value <= 0:
                raise ConfigFormatError(f"{name} must be greater than zero")

    def _toml_lines(self) -> list[str]:
        lines = ["[[rules.required]]", f"id = {_toml_string(self.id)}"]
        if self.within_lines is not None:
            lines.append(f"withinLines = {self.within_lines}")
        if self.within_columns is not None:
            lines.append(f"withinColumns = {self.within_columns}")
        return lines


@dataclass(frozen=True)
class Rule:
    """Betterleaks `[[rules]]` detection rule."""

    id: str
    description: str
    regex: Optional[str] = None
    keywords: list[str] = field(default_factory=list)
    path: Optional[str] = None
    secret_group: Optional[int] = None
    entropy: Optional[float] = None
    tags: list[str] = field(default_factory=list)
    specificity: Optional[int] = None
    filter: Optional[ExprInput] = None
    validate: Optional[ExprInput] = None
    required: list[RequiredRule] = field(default_factory=list)
    skip_report: bool = False
    token_efficiency: bool = False

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ConfigFormatError("rule id cannot be empty")
        if not self.description.strip():
            raise ConfigFormatError(f"{self.id}: rule description cannot be empty")
        if self.regex is None and self.path is None:
            raise ConfigFormatError(f"{self.id}: rule must define regex or path")
        if self.secret_group is not None and self.secret_group < 0:
            raise ConfigFormatError(f"{self.id}: secret_group cannot be negative")
        if self.entropy is not None and self.entropy <= 0:
            raise ConfigFormatError(f"{self.id}: entropy must be greater than zero")
        if self.specificity is not None and self.specificity < 0:
            raise ConfigFormatError(f"{self.id}: specificity cannot be negative")

    @classmethod
    def regex_rule(
        cls,
        *,
        id: str,
        description: str,
        regex: str,
        keywords: Optional[list[str]] = None,
        secret_group: Optional[int] = None,
        tags: Optional[list[str]] = None,
        filter: Optional[ExprInput] = None,
        validate: Optional[ExprInput] = None,
        entropy: Optional[float] = None,
    ) -> "Rule":
        """Create a common regex-based rule with ergonomic defaults."""
        return cls(
            id=id,
            description=description,
            regex=regex,
            keywords=keywords or [],
            secret_group=secret_group,
            tags=tags or [],
            filter=filter,
            validate=validate,
            entropy=entropy,
        )

    @classmethod
    def prefixed_token_rule(
        cls,
        *,
        id: str,
        description: str,
        prefix: str,
        token_pattern: str = r"[A-Za-z0-9_\-]{16,}",
        keywords: Optional[list[str]] = None,
        secret_group: Optional[int] = None,
        tags: Optional[list[str]] = None,
        filter: Optional[ExprInput] = None,
        validate: Optional[ExprInput] = None,
        entropy: Optional[float] = None,
    ) -> "Rule":
        """Create a regex rule for a token with a literal prefix."""
        _ensure_non_empty("token prefix", prefix)
        _ensure_non_empty("token pattern", token_pattern)
        return cls.regex_rule(
            id=id,
            description=description,
            regex=re.escape(prefix) + token_pattern,
            keywords=keywords if keywords is not None else [prefix],
            secret_group=secret_group,
            tags=tags,
            filter=filter,
            validate=validate,
            entropy=entropy,
        )

    @classmethod
    def pem_private_key_rule(
        cls,
        *,
        id: str = "pem-private-key",
        description: str = "PEM private key",
        path: Optional[str] = None,
        tags: Optional[list[str]] = None,
        filter: Optional[ExprInput] = None,
    ) -> "Rule":
        """Create a rule for PEM private key blocks."""
        return cls(
            id=id,
            description=description,
            regex=r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----",
            path=path,
            keywords=["PRIVATE KEY"],
            tags=tags or ["key", "private-key"],
            filter=filter,
        )

    @classmethod
    def path_rule(
        cls,
        *,
        id: str,
        description: str,
        path: str,
        tags: Optional[list[str]] = None,
        filter: Optional[ExprInput] = None,
    ) -> "Rule":
        """Create a path-only rule for file/path based findings."""
        return cls(
            id=id,
            description=description,
            path=path,
            tags=tags or [],
            filter=filter,
        )

    def _toml_lines(self) -> list[str]:
        lines = [
            "[[rules]]",
            f"id = {_toml_string(self.id)}",
            f"description = {_toml_string(self.description)}",
        ]
        if self.path is not None:
            lines.append(f"path = {_toml_string(self.path)}")
        if self.regex is not None:
            lines.append(f"regex = {_toml_string(self.regex)}")
        if self.secret_group is not None:
            lines.append(f"secretGroup = {self.secret_group}")
        if self.entropy is not None:
            lines.append(f"entropy = {_toml_float(self.entropy)}")
        if self.keywords:
            lines.append(f"keywords = {_toml_string_list(self.keywords)}")
        if self.tags:
            lines.append(f"tags = {_toml_string_list(self.tags)}")
        if self.specificity is not None:
            lines.append(f"specificity = {self.specificity}")
        filter_expr = _expr_value(self.filter)
        if filter_expr is not None:
            lines.append(f"filter = {_toml_string(filter_expr)}")
        validate_expr = _expr_value(self.validate)
        if validate_expr is not None:
            lines.append(f"validate = {_toml_string(validate_expr)}")
        if self.skip_report:
            lines.append(f"skipReport = {_toml_bool(self.skip_report)}")
        if self.token_efficiency:
            lines.append(f"tokenEfficiency = {_toml_bool(self.token_efficiency)}")
        for required_rule in self.required:
            lines.append("")
            lines.extend(required_rule._toml_lines())
        return lines


@dataclass(frozen=True)
class BetterleaksConfig:
    """Typed Python representation of a Betterleaks TOML config."""

    rules: list[Rule] = field(default_factory=list)
    title: Optional[str] = None
    description: Optional[str] = None
    extend: Optional[Extend] = None
    prefilter: Optional[ExprInput] = None
    filter: Optional[ExprInput] = None
    min_version: Optional[str] = None
    betterleaks_min_version: Optional[str] = None
    extend_base_path: Optional[PathInput] = None

    def __post_init__(self) -> None:
        seen_rules: set[str] = set()
        for rule in self.rules:
            if rule.id in seen_rules:
                raise ConfigFormatError(f"duplicate rule id: {rule.id}")
            seen_rules.add(rule.id)
        if not self.rules and (self.extend is None or self.extend._is_empty()):
            raise ConfigFormatError("config must define rules or extend another config")

    @classmethod
    def with_defaults(
        cls,
        *,
        rules: Optional[list[Rule]] = None,
        disabled_rules: Optional[list[str]] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        prefilter: Optional[ExprInput] = None,
        filter: Optional[ExprInput] = None,
        min_version: Optional[str] = None,
        betterleaks_min_version: Optional[str] = None,
    ) -> "BetterleaksConfig":
        """Create a config that extends Betterleaks' bundled defaults."""
        return cls(
            rules=rules or [],
            extend=Extend(use_default=True, disabled_rules=disabled_rules or []),
            title=title,
            description=description,
            prefilter=prefilter,
            filter=filter,
            min_version=min_version,
            betterleaks_min_version=betterleaks_min_version,
        )

    def to_toml(self, *, extend_base_path: Optional[PathInput] = None) -> str:
        """Serialize this config to Betterleaks-compatible TOML."""
        lines: list[str] = []
        if self.title is not None:
            lines.append(f"title = {_toml_string(self.title)}")
        if self.description is not None:
            lines.append(f"description = {_toml_string(self.description)}")
        if self.min_version is not None:
            lines.append(f"minVersion = {_toml_string(self.min_version)}")
        if self.betterleaks_min_version is not None:
            lines.append(f"betterleaksMinVersion = {_toml_string(self.betterleaks_min_version)}")
        prefilter_expr = _expr_value(self.prefilter)
        if prefilter_expr is not None:
            lines.append(f"prefilter = {_toml_string(prefilter_expr)}")
        filter_expr = _expr_value(self.filter)
        if filter_expr is not None:
            lines.append(f"filter = {_toml_string(filter_expr)}")

        if self.extend is not None and not self.extend._is_empty():
            if lines:
                lines.append("")
            lines.extend(
                self.extend._toml_lines(
                    base_path=extend_base_path
                    if extend_base_path is not None
                    else self.extend_base_path
                )
            )

        for rule in self.rules:
            if lines:
                lines.append("")
            lines.extend(rule._toml_lines())

        return "\n".join(lines).rstrip() + "\n"

    def write(self, path: PathInput) -> Path:
        """Write this config to `path` and return the resolved `Path`."""
        config_path = Path(path)
        config_path.write_text(self.to_toml(extend_base_path=config_path.parent), encoding="utf-8")
        return config_path


def _resolve_extend_path(path: PathInput, base_path: Optional[PathInput]) -> str:
    candidate = Path(path)
    if base_path is not None and not candidate.is_absolute():
        candidate = Path(base_path) / candidate
    return os.fspath(candidate)
