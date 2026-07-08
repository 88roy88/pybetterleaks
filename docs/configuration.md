# Configuration

PyBetterleaks v0.2 adds a typed Python config builder that serializes to a
temporary Betterleaks TOML file for each scan. The Go bridge still receives a
`config_path`, so Betterleaks remains the source of truth for config parsing and
rule behavior.

Use `config_path` when you already have a hand-written Betterleaks config. Use
`BetterleaksConfig` when application code needs to generate or adjust rules.

## Minimal Custom Config

```python
from pybetterleaks import BetterleaksConfig, Rule, scan_text

config = BetterleaksConfig(
    rules=[
        Rule(
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
        Rule(
            id="internal-token",
            description="Internal service token",
            regex=r"INTERNAL_[A-Z0-9]{16}",
            keywords=["INTERNAL_"],
        )
    ],
    disabled_rules=["generic-api-key"],
)
```

## Expr Filters And Validation

Betterleaks uses Expr for `prefilter`, `filter`, and `validate`. PyBetterleaks
stores those expressions as raw strings through the `Expr` helper:

```python
from pybetterleaks import BetterleaksConfig, Expr, Rule

config = BetterleaksConfig(
    prefilter=Expr('!filter.matchesAny(get(attributes, "path", ""), [`^vendor/`])'),
    rules=[
        Rule(
            id="internal-token",
            description="Internal service token",
            regex=r"INTERNAL_[A-Z0-9]{16}",
            keywords=["INTERNAL_"],
            filter=Expr('filter.containsAny(finding["secret"], ["_TEST_"])'),
            validate=Expr('{"result": "needs_validation"}'),
        )
    ],
)
```

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

## Supported v0.2 Fields

Top-level:

- `title`
- `description`
- `min_version`
- `betterleaks_min_version`
- `prefilter`
- `filter`
- `extend`
- `rules`

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

Legacy Betterleaks allowlists are intentionally omitted. Modern configs should
use Expr `prefilter` and `filter` expressions instead, matching upstream
Betterleaks documentation.
