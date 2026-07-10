# Configuration

PyBetterleaks includes a typed Python config builder that serializes to
Betterleaks-compatible TOML for each scan. The Python SDK sends that TOML string
through the JSON ABI, and the Go bridge parses it with Betterleaks'
`config.ParseTOMLString`, so Betterleaks remains the source of truth for config
parsing and rule behavior.

Use `config_path` when you already have a hand-written Betterleaks config. Use
`BetterleaksConfig` when application code needs to generate or adjust rules.

## Minimal Custom Config

```python
from pybetterleaks import BetterleaksConfig, Rule, scan_text

config = BetterleaksConfig(
    rules=[
        Rule.regex_rule(
            id="internal-token",
            description="Internal service token",
            regex=r"INTERNAL_[A-Z0-9]{16}",
            keywords=["INTERNAL_"],
        )
    ]
)

result = scan_text("INTERNAL_0123456789ABCDEF", config=config)
```

Passing both `config` and `config_path` raises `ValueError`.

## Extending Betterleaks Defaults

`BetterleaksConfig.with_defaults()` creates a config with `[extend]` and
`useDefault = true`:

```python
from pybetterleaks import BetterleaksConfig, Rule

config = BetterleaksConfig.with_defaults(
    rules=[
        Rule.regex_rule(
            id="internal-token",
            description="Internal service token",
            regex=r"INTERNAL_[A-Z0-9]{16}",
            keywords=["INTERNAL_"],
        )
    ],
    disabled_rules=["generic-api-key"],
)
```

## Expr Filters

Betterleaks uses Expr for `prefilter`, `filter`, and `validate`.
PyBetterleaks stores those expressions as strings and provides helper builders
for the common patterns.

```python
from pybetterleaks import BetterleaksConfig, Expr, Rule, Validation

config = BetterleaksConfig(
    prefilter=Expr.not_(Expr.path_matches_any([r"^vendor/"])),
    rules=[
        Rule.regex_rule(
            id="internal-token",
            description="Internal service token",
            regex=r"INTERNAL_[A-Z0-9]{16}",
            keywords=["INTERNAL_"],
            filter=Expr.finding_contains_any(["_TEST_"]),
            validate=Validation.needs_validation(),
        )
    ],
)
```

You can still pass raw Expr source with `Expr("...")` or a plain string when a
helper does not cover the shape you need.

Common filter helpers:

- `Expr.min_entropy(threshold, field="secret")`
- `Expr.token_efficiency(field="secret")`
- `Expr.finding_contains_any(values, field="secret")`
- `Expr.finding_matches_any(patterns, field="secret")`
- `Expr.attribute_contains_any(name, values, default="")`
- `Expr.attribute_matches_any(name, patterns, default="")`
- `Expr.path_matches_any(patterns)`
- `Expr.git_commit_in(commits)`
- `Expr.any_of(...)`, `Expr.all_of(...)`, and `Expr.not_(...)`
- `Expr.finding(field)` and `Expr.attribute(name)` for composing raw
  expressions

The allowlist-style helpers intentionally emit modern Betterleaks filters:

```python
Expr.path_matches_any([r"^vendor/"])
```

```text
filter.matchesAny(get(attributes, "path", ""), [`^vendor/`])
```

Legacy Betterleaks allowlists are intentionally omitted. Modern configs should
use Expr `prefilter` and `filter` expressions instead, matching upstream
Betterleaks documentation.

## Validation Helpers

`Validation` creates structured Betterleaks validation results:

```python
from pybetterleaks import BetterleaksConfig, Rule, Validation

config = BetterleaksConfig(
    rules=[
        Rule.prefixed_token_rule(
            id="example-token",
            description="Example token",
            prefix="EXAMPLE_",
            validate=Validation.needs_validation(provider="example"),
        )
    ]
)
```

Supported helpers:

- `Validation.valid(**metadata)`
- `Validation.invalid(reason=None, **metadata)`
- `Validation.unknown(response_expr=None, **metadata)`
- `Validation.needs_validation(**metadata)`
- `Validation.bearer_get(...)` for a common bearer-token HTTP GET validator

For provider-specific validation logic, pass raw Expr. The helper surface is
for safe composition, not a replacement for Betterleaks' validation language.

Validation environment variables must be explicitly allowlisted:

```python
result = scan_text(
    "INTERNAL_0123456789ABCDEF",
    config=config,
    validation=True,
    validation_env_vars=["GITHUB_BASE_URL"],
)
```

The Python layer sends values only for names listed in `validation_env_vars`.
The Go bridge temporarily mirrors those values into the Go process environment
while the scan runs, because Betterleaks validation reads env vars from Go.

## Entropy And Token Filters

Betterleaks filters return `True` when a finding should be skipped. The
`Expr.min_entropy()` helper hides that inversion:

```python
from pybetterleaks import BetterleaksConfig, Expr, Rule

config = BetterleaksConfig(
    rules=[
        Rule.regex_rule(
            id="high-entropy-token",
            description="High entropy token",
            regex=r"TOKEN_[A-Za-z0-9]{32}",
            filter=Expr.min_entropy(3.5),
        )
    ]
)
```

`Rule.entropy` is also supported for compatibility with Betterleaks'
`entropy = ...` TOML field. Prefer `Expr.min_entropy()` for new configs because
upstream Betterleaks translates legacy entropy fields into filters internally.

Use `Expr.token_efficiency()` when you want Betterleaks to skip natural-language
text that tokenizes too efficiently to look like a random secret.

## Rule Helpers

Use the base `Rule(...)` dataclass when you want direct field control. Use
helper constructors for common rule shapes:

```python
from pybetterleaks import BetterleaksConfig, Rule

config = BetterleaksConfig(
    rules=[
        Rule.regex_rule(
            id="internal-token",
            description="Internal service token",
            regex=r"INTERNAL_[A-Z0-9]{16}",
            keywords=["INTERNAL_"],
        ),
        Rule.path_rule(
            id="private-key-path",
            description="Private key path",
            path=r"private-key\.pem$",
        ),
        Rule.prefixed_token_rule(
            id="prefixed-token",
            description="Prefixed token",
            prefix="tok_",
            token_pattern=r"[A-Za-z0-9]{24,}",
        ),
        Rule.pem_private_key_rule(),
    ]
)
```

## Relative Extend Paths

Inline configs do not have a file path of their own. If you need `[extend]` to
load a relative local file, set `extend_base_path` or write the config to disk:

```python
from pybetterleaks import BetterleaksConfig, Extend

config = BetterleaksConfig(
    extend=Extend(path="base.toml"),
    extend_base_path="/repo/config",
)

toml = config.to_toml()
```

The serialized `extend.path` becomes `/repo/config/base.toml`. When calling
`config.write(path)`, relative `extend.path` values are resolved against the
written config file's parent directory.

## Supported Fields

Top-level:

- `title`
- `description`
- `min_version`
- `betterleaks_min_version`
- `prefilter`
- `filter`
- `extend`
- `rules`
- `extend_base_path` (Python-only helper for serializing relative
  `extend.path`)

`Extend`:

- `path`
- `url`
- `use_default`
- `disabled_rules`

`Rule`:

- `id`
- `description`
- `regex`
- `path`
- `secret_group`
- `entropy`
- `keywords`
- `tags`
- `specificity`
- `filter`
- `validate`
- `required`
- `skip_report`
- `token_efficiency`

`RequiredRule`:

- `id`
- `within_lines`
- `within_columns`
