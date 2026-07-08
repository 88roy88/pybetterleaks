from __future__ import annotations

import json
import os
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


ExprInput = Union[str, Expr]


def _expr_value(value: Optional[ExprInput]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, Expr):
        return value.value
    return str(value)


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

    def _toml_lines(self) -> list[str]:
        lines = ["[extend]"]
        if self.path is not None:
            lines.append(f"path = {_toml_string(os.fspath(self.path))}")
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
        if self.specificity is not None and self.specificity < 0:
            raise ConfigFormatError(f"{self.id}: specificity cannot be negative")

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

    def to_toml(self) -> str:
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
            lines.extend(self.extend._toml_lines())

        for rule in self.rules:
            if lines:
                lines.append("")
            lines.extend(rule._toml_lines())

        return "\n".join(lines).rstrip() + "\n"

    def write(self, path: PathInput) -> Path:
        """Write this config to `path` and return the resolved `Path`."""
        config_path = Path(path)
        config_path.write_text(self.to_toml(), encoding="utf-8")
        return config_path
