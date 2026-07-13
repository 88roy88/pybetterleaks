# PyBetterleaks

![PyBetterleaks: Python-native Betterleaks with bundled platform wheels and no runtime subprocess](https://raw.githubusercontent.com/roymezan/pybetterleaks/main/docs/assets/readme-hero.svg)

[![PyPI](https://img.shields.io/pypi/v/pybetterleaks.svg)](https://pypi.org/project/pybetterleaks/)
[![Python](https://img.shields.io/pypi/pyversions/pybetterleaks.svg)](https://pypi.org/project/pybetterleaks/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Wheels](https://img.shields.io/badge/wheels-self--contained-success.svg)](#platforms)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-teal.svg)](https://roymezan.github.io/pybetterleaks/)

Python-native Betterleaks. No CLI wrapper. No Go toolchain in your runtime
image. No runtime `subprocess`.

```bash
pip install pybetterleaks
```

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
for finding in result.findings:
    print(f"{finding.rule_id}: {finding.secret}")
```

PyBetterleaks wraps the Betterleaks Go engine through a tiny `ctypes` JSON ABI
and returns typed Python dataclasses. It is built for CI jobs, Python services,
notebooks, agent tools, and Docker images that should stay simple.

> Status: alpha. PyPI wheels are published for CPython 3.9-3.15 on supported
> glibc Linux, macOS, and Windows targets. Musllinux/Alpine remains unsupported
> for the current Go `c-shared` design; see
> [Platforms](#platforms).

## Getting Started

From a checkout:

```bash
uv sync --all-extras --dev
uv run python scripts/build_native.py
uv run coverage run -m pytest
uv run coverage report
```

Run a scan with the bundled Betterleaks defaults:

```bash
uv run python - <<'PY'
from pybetterleaks import betterleaks_version, scan_text

print("Betterleaks:", betterleaks_version())

result = scan_text(
    "AGE-SECRET-KEY-"
    + "1QPZRY9X8GF2TVDW0S3JN54KHCE6MUA7LQPZRY9X8GF2TVDW0S3JN54KHCE"
)

for finding in result.findings:
    print(f"{finding.rule_id}: {finding.secret}")
PY
```

Expected output:

```text
Betterleaks: v1.6.1
age-secret-key: REDACTED
```

The example secrets are synthetic fixtures.

## Why Not Subprocess?

Shelling out is fine for one script. It becomes awkward as an SDK boundary:

- process output becomes the API contract
- quoting and path behavior leak into user code
- Docker images need extra binaries
- errors are process-shaped instead of Python-shaped
- async and agent workflows pay process startup overhead

PyBetterleaks keeps the Betterleaks engine native and gives Python an importable
API:

```text
Python app
  -> pybetterleaks
    -> ctypes JSON ABI
      -> bundled Go shared library
        -> Betterleaks
```

## API

```python
from pybetterleaks import SUPPORTED_GIT_SCOPES, betterleaks_version, scan_dir, scan_git, scan_text

print(betterleaks_version())
print(SUPPORTED_GIT_SCOPES)

text_result = scan_text("token goes here", validation=False, redact=True)
dir_result = scan_dir(".", config_path=".betterleaks.toml")
git_result = scan_git(".", scope="worktree", config_path=".betterleaks.toml")
```

`scan_git` currently supports local worktree scans. It validates that the target
is inside a Git worktree, skips `.git` metadata, and does not invoke the Git
executable. The supported scope is explicit: `SUPPORTED_GIT_SCOPES ==
("worktree",)`.

Programmatic config uses Betterleaks' TOML concepts directly, with helpers for
filters, validation results, common rule shapes, and relative `extend.path`
handling:

```python
from pybetterleaks import BetterleaksConfig, Expr, Rule, Validation, scan_dir

config = BetterleaksConfig.with_defaults(
    rules=[
        Rule.regex_rule(
            id="internal-token",
            description="Internal service token",
            regex=r"INTERNAL_[A-Z0-9]{16}",
            keywords=["INTERNAL_"],
            filter=Expr.min_entropy(3.5),
            validate=Validation.needs_validation(provider="internal"),
        )
    ],
    disabled_rules=["generic-api-key"],
)

result = scan_dir("src", config=config, validation=True)
```

Async wrappers run the blocking native scan in an executor and request
cooperative cancellation from the Go bridge when the task is cancelled:

```python
import asyncio
from pybetterleaks import scan_text_async

async def main() -> None:
    result = await scan_text_async("INTERNAL_0123456789ABCDEF", timeout_seconds=5)
    print(result.ok, len(result.findings))

asyncio.run(main())
```

## Docker

```dockerfile
FROM python:3.12-slim

RUN pip install --only-binary=:all: pybetterleaks

COPY . /app
WORKDIR /app

CMD ["python", "scan.py"]
```

No `go install`. No Betterleaks CLI. No install-time binary downloads.

## Platforms

Target wheel matrix:

| Platform | Status |
| --- | --- |
| Linux x86_64 | manylinux wheels published |
| macOS arm64 | macOS 11+ wheels published |
| macOS x86_64 | macOS 11+ wheels published |
| Windows amd64 | win_amd64 wheels published |
| Linux arm64 | future CI capacity |
| Alpine/musllinux | unsupported; no wheels published |

Previous Alpine experiments failed while loading the Go shared library through
Python `ctypes` on musl:

```text
initial-exec TLS resolves to dynamic definition
```

This is a Go + musl shared-library loader limitation, not a missing Docker
package. The same failure reproduces with Go `c-shared` and a Go `c-archive`
linked into a musl shared object, so the project will not publish musllinux
wheels until that loader path is fixed. Use Debian/Ubuntu-style glibc Python
images, such as `python:3.12-slim`, for supported Linux runtime images.
Track musllinux work in
[issue #1](https://github.com/roymezan/pybetterleaks/issues/1).

## Local Development

```bash
uv sync --all-extras --dev
uv run python scripts/build_native.py
uv run coverage run -m pytest
uv run coverage report
uv run ruff check .
uv run mypy python
uv run --group docs mkdocs build --strict
```

Build a local wheel after the native library exists:

```bash
uv build --wheel
```

Run the Docker packaging E2E:

```bash
bash e2e/run.sh
```

Verify the published PyPI wheel in a temporary virtual environment:

```bash
uv run python scripts/pypi_smoke.py
```

## Benchmarks

Synthetic benchmarks live in `benchmarks/`:

```bash
uv run python benchmarks/bench.py --rounds 10 --files 50 --secrets-per-file 2
```

To compare against a local Betterleaks CLI:

```bash
uv run python benchmarks/bench.py --cli --cli-path /path/to/betterleaks
```

README numbers will stay blank until they are measured on release hardware.
No fake charts.

## Security And Supply Chain

- Betterleaks is pinned in `bridge/go.mod`
- the bundled Betterleaks pin is documented in `docs/betterleaks-pin.md`
- CI checks that `go.mod`, `go.sum`, and the bridge version constant agree
- wheels are built in GitHub Actions
- release artifacts get SHA256 checksums and checksum verification
- GitHub releases attach `SHA256SUMS`
- GitHub artifact attestations tie wheels back to the release workflow
- PyPI publication uses trusted publishing
- runtime installs never download native binaries
- wheel smoke tests import the package, run `betterleaks_version()`, scan text,
  and exercise typed config plus async wrappers
- Docker E2E installs a locally built wheel into a no-Go runtime image
- post-publish smoke tests install from PyPI in a temporary virtual environment
