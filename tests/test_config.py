from pathlib import Path
from typing import Any

import pytest
from pybetterleaks import (
    BetterleaksConfig,
    ConfigFormatError,
    Expr,
    Extend,
    RequiredRule,
    Rule,
)

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


def parse_toml(value: str) -> dict[str, Any]:
    return tomllib.loads(value)


def test_config_serializes_modern_betterleaks_toml() -> None:
    config = BetterleaksConfig(
        title="PyBetterleaks v0.2",
        description="Synthetic config",
        betterleaks_min_version="v1.6.1",
        prefilter=Expr('!filter.matchesAny(get(attributes, "path", ""), [`^vendor/`])'),
        filter='filter.containsAny(finding["secret"], ["_TEST_"])',
        extend=Extend(use_default=True, disabled_rules=["example-disabled-rule"]),
        rules=[
            Rule(
                id="internal-token",
                description="Internal service token",
                regex=r"INTERNAL_[A-Z0-9]{16}",
                keywords=["INTERNAL_"],
                tags=["internal", "token"],
                secret_group=0,
                specificity=250,
                validate='{"result": "needs_validation"}',
                required=[RequiredRule(id="internal-prefix", within_lines=3)],
            )
        ],
    )

    parsed = parse_toml(config.to_toml())

    assert parsed["title"] == "PyBetterleaks v0.2"
    assert parsed["betterleaksMinVersion"] == "v1.6.1"
    assert parsed["extend"]["useDefault"] is True
    assert parsed["extend"]["disabledRules"] == ["example-disabled-rule"]
    assert parsed["rules"][0]["id"] == "internal-token"
    assert parsed["rules"][0]["keywords"] == ["INTERNAL_"]
    assert parsed["rules"][0]["secretGroup"] == 0
    assert parsed["rules"][0]["required"][0]["id"] == "internal-prefix"
    assert parsed["rules"][0]["required"][0]["withinLines"] == 3


def test_config_with_defaults_helper() -> None:
    config = BetterleaksConfig.with_defaults(
        rules=[
            Rule(
                id="pybetterleaks-custom",
                description="Custom fixture",
                regex=r"PYBETTERLEAKS_CUSTOM_[A-Z0-9]{16}",
                keywords=["PYBETTERLEAKS_CUSTOM_"],
            )
        ],
        disabled_rules=["generic-api-key"],
    )

    parsed = parse_toml(config.to_toml())

    assert parsed["extend"]["useDefault"] is True
    assert parsed["extend"]["disabledRules"] == ["generic-api-key"]


def test_config_rejects_duplicate_rules() -> None:
    rule = Rule(id="duplicate", description="Duplicate", regex="DUPLICATE")

    with pytest.raises(ConfigFormatError, match="duplicate"):
        BetterleaksConfig(rules=[rule, rule])


def test_config_write_returns_path(tmp_path: Path) -> None:
    config = BetterleaksConfig(
        rules=[
            Rule(
                id="write-test",
                description="Write test",
                regex=r"WRITE_[A-Z0-9]{16}",
            )
        ]
    )

    path = config.write(tmp_path / "betterleaks.toml")

    assert path == tmp_path / "betterleaks.toml"
    assert "write-test" in path.read_text(encoding="utf-8")
