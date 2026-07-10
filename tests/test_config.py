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
    Validation,
)

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


def parse_toml(value: str) -> dict[str, Any]:
    return tomllib.loads(value)


def test_config_serializes_modern_betterleaks_toml() -> None:
    config = BetterleaksConfig(
        title="PyBetterleaks v0.4",
        description="Synthetic config",
        betterleaks_min_version="v1.6.1",
        prefilter=Expr.not_(Expr.path_matches_any([r"^vendor/"])),
        filter=Expr.finding_contains_any(["_TEST_"]),
        extend=Extend(use_default=True, disabled_rules=["example-disabled-rule"]),
        rules=[
            Rule(
                id="internal-token",
                description="Internal service token",
                regex=r"INTERNAL_[A-Z0-9]{16}",
                keywords=["INTERNAL_"],
                tags=["internal", "token"],
                secret_group=0,
                entropy=3.5,
                specificity=250,
                validate='{"result": "needs_validation"}',
                required=[RequiredRule(id="internal-prefix", within_lines=3)],
            )
        ],
    )

    parsed = parse_toml(config.to_toml())

    assert parsed["title"] == "PyBetterleaks v0.4"
    assert parsed["betterleaksMinVersion"] == "v1.6.1"
    assert parsed["extend"]["useDefault"] is True
    assert parsed["extend"]["disabledRules"] == ["example-disabled-rule"]
    assert parsed["rules"][0]["id"] == "internal-token"
    assert parsed["rules"][0]["keywords"] == ["INTERNAL_"]
    assert parsed["rules"][0]["secretGroup"] == 0
    assert parsed["rules"][0]["entropy"] == 3.5
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


def test_expr_min_entropy_helper_uses_betterleaks_filter_semantics() -> None:
    expr = Expr.min_entropy(3.5)

    assert str(expr) == 'filter.entropy(finding["secret"]) <= 3.5'


def test_expr_helpers_cover_modern_allowlist_replacements() -> None:
    assert str(Expr.path_matches_any([r"vendor/"])) == (
        'filter.matchesAny(get(attributes, "path", ""), [`vendor/`])'
    )
    assert str(Expr.git_commit_in(["abc123"])) == 'get(attributes, "git.sha", "") in ["abc123"]'
    assert str(Expr.finding_matches_any([r"foo.+bar"], field="line")) == (
        'filter.matchesAny(finding["line"], [`foo.+bar`])'
    )
    assert str(Expr.finding_contains_any(["example"])) == (
        'filter.containsAny(finding["secret"], ["example"])'
    )
    assert str(Expr.any_of(Expr.min_entropy(3), Expr.token_efficiency())) == (
        "(filter.entropy(finding[\"secret\"]) <= 3.0) || "
        "(filter.failsTokenEfficiency(finding[\"secret\"]))"
    )
    assert str(Expr.all_of(Expr.path_matches_any([r"\.env$"]), Expr.min_entropy(3.5))) == (
        '(filter.matchesAny(get(attributes, "path", ""), [`\\.env$`])) && '
        '(filter.entropy(finding["secret"]) <= 3.5)'
    )


def test_validation_helpers_serialize_common_validation_expressions() -> None:
    assert str(Validation.valid(provider="example")) == (
        '{"result":"valid","provider":"example"}'
    )
    assert str(Validation.invalid(reason="Unauthorized")) == (
        '{"result":"invalid","reason":"Unauthorized"}'
    )
    assert str(Validation.unknown("r")) == "validate.unknown(r)"
    assert str(Validation.needs_validation()) == '{"result":"needs_validation"}'

    bearer = str(Validation.bearer_get("https://api.example.test/user", 'r.body contains "ok"'))

    assert 'http.get("https://api.example.test/user"' in bearer
    assert '"Authorization": "Bearer " + finding["secret"]' in bearer
    assert 'r.status == 200 && (r.body contains "ok")' in bearer
    assert 'validate.unknown(r)' in bearer


def test_rule_helpers_serialize_expected_toml() -> None:
    config = BetterleaksConfig(
        rules=[
            Rule.regex_rule(
                id="helper-token",
                description="Helper token",
                regex=r"HELPER_[A-Z0-9]{16}",
                keywords=["HELPER_"],
                filter=Expr.min_entropy(3),
                entropy=3,
            ),
            Rule.path_rule(
                id="private-key-path",
                description="Private key path",
                path=r"private-key\.pem$",
                tags=["key"],
            ),
            Rule.prefixed_token_rule(
                id="prefixed-token",
                description="Prefixed token",
                prefix="tok_",
                token_pattern=r"[A-Z0-9]{16}",
            ),
            Rule.pem_private_key_rule(),
        ]
    )

    parsed = parse_toml(config.to_toml())

    assert parsed["rules"][0]["id"] == "helper-token"
    assert parsed["rules"][0]["filter"] == 'filter.entropy(finding["secret"]) <= 3.0'
    assert parsed["rules"][0]["entropy"] == 3.0
    assert parsed["rules"][1]["path"] == r"private-key\.pem$"
    assert parsed["rules"][2]["regex"] == r"tok_[A-Z0-9]{16}"
    assert parsed["rules"][2]["keywords"] == ["tok_"]
    assert parsed["rules"][3]["id"] == "pem-private-key"
    assert parsed["rules"][3]["keywords"] == ["PRIVATE KEY"]


def test_config_rejects_duplicate_rules() -> None:
    rule = Rule(id="duplicate", description="Duplicate", regex="DUPLICATE")

    with pytest.raises(ConfigFormatError, match="duplicate"):
        BetterleaksConfig(rules=[rule, rule])


def test_config_rejects_invalid_entropy_values() -> None:
    with pytest.raises(ConfigFormatError, match="entropy"):
        Expr.min_entropy(0)

    with pytest.raises(ConfigFormatError, match="entropy"):
        Rule(id="bad-entropy", description="Bad entropy", regex="BAD", entropy=0)


def test_config_rejects_empty_expr_helper_inputs() -> None:
    with pytest.raises(ConfigFormatError, match="regex list"):
        Expr.path_matches_any([])

    with pytest.raises(ConfigFormatError, match="token prefix"):
        Rule.prefixed_token_rule(id="bad", description="Bad", prefix="")

    with pytest.raises(ConfigFormatError, match="metadata"):
        Validation.unknown("r", detail="ignored")


def test_inline_config_resolves_relative_extend_path_with_base_path(tmp_path: Path) -> None:
    config = BetterleaksConfig(
        extend=Extend(path="base.toml"),
        extend_base_path=tmp_path,
    )

    parsed = parse_toml(config.to_toml())

    assert parsed["extend"]["path"] == str(tmp_path / "base.toml")


def test_config_write_returns_path(tmp_path: Path) -> None:
    config = BetterleaksConfig(
        extend=Extend(path="base.toml"),
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
    parsed = parse_toml(path.read_text(encoding="utf-8"))
    assert parsed["extend"]["path"] == str(tmp_path / "base.toml")
    assert parsed["rules"][0]["id"] == "write-test"
