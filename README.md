# PyBetterleaks

[![PyPI](https://img.shields.io/pypi/v/pybetterleaks.svg)](https://pypi.org/project/pybetterleaks/)
[![Python](https://img.shields.io/pypi/pyversions/pybetterleaks.svg)](https://pypi.org/project/pybetterleaks/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Wheels](https://img.shields.io/badge/wheels-self--contained-success.svg)](#platforms)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-teal.svg)](https://88roy88.github.io/pybetterleaks/)

Python-native Betterleaks. No CLI dance. No Go toolchain in your Docker image.
No runtime `subprocess`.

```bash
pip install pybetterleaks
```

```python
from pybetterleaks import scan_text

secret = "AGE-SECRET-KEY-" + "1QPZRY9X8GF2TVDW0S3JN54KHCE6MUA7LQPZRY9X8GF2TVDW0S3JN54KHCE"
result = scan_text(secret)

for finding in result.findings:
    print(f"{finding.rule_id}: {finding.secret}")
```

PyBetterleaks wraps the Betterleaks Go engine through a tiny native bridge and
returns typed Python dataclasses. It is built for the places security scanning
actually happens: CI jobs, Python services, notebooks, agent tools, and Docker
images that should stay boring.

> Status: early scaffold. The Python SDK, packaging, CI, and native ABI are in
> place. The macOS arm64 native bridge has been compiled and smoke-tested
> locally; Linux and Windows wheels are built by CI.

## Getting Started

You can use the SDK locally from this repository today:

```bash
uv sync --all-extras --dev
uv run python scripts/build_native.py
```

Then run a scan:

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

The example secret is intentionally fake. Public `pip install pybetterleaks`
comes after the wheel matrix is published to PyPI.

## Why This Exists

Betterleaks is fast and serious. Python is everywhere. The awkward bit is the
boundary between them.

Shelling out to a scanner works for scripts, but it gets old fast in a real SDK:

- quoting and path handling become your problem
- process output becomes an API surface
- Docker images need extra binaries
- errors are process-shaped instead of Python-shaped
- async and agent workflows pay a needless process tax

PyBetterleaks keeps the engine native and gives Python a clean importable API.

```text
Python app
  -> pybetterleaks
    -> ctypes JSON ABI
      -> bundled Go shared library
        -> Betterleaks
```

## Install

Released wheels are intended to be self-contained after publication:

```bash
pip install pybetterleaks
```

For production Docker images, prefer binary-only installs:

```bash
pip install --only-binary=:all: pybetterleaks
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

## API

```python
from pybetterleaks import betterleaks_version, scan_dir, scan_text

print(betterleaks_version())

text_result = scan_text("token goes here", validation=False, redact=True)
dir_result = scan_dir(".", config_path=".betterleaks.toml")
```

The public result type is a dataclass:

```python
@dataclass(frozen=True)
class ScanResult:
    findings: list[Finding]
    errors: list[ScanError]
    betterleaks_version: str
```

## Platforms

Target wheel matrix for the first release:

| Platform | Wheel |
| --- | --- |
| Linux x86_64 | manylinux |
| Linux arm64 | manylinux, when CI support is available |
| macOS arm64 | macOS 11+ |
| macOS x86_64 | macOS 11+ |
| Windows amd64 | win_amd64 |

Alpine/musllinux is intentionally deferred until the normal Linux wheels are
stable.

## Local Development

This project uses `uv`.

```bash
uv sync --all-extras --dev
uv run pytest
uv run ruff check .
uv run mypy python
uv run --group docs mkdocs build --strict
```

Build the native library when Go is installed:

```bash
uv run python scripts/build_native.py
```

Build a local wheel after the native library exists:

```bash
uv build --wheel
```

Source distributions intentionally exclude generated native libraries. The
release path publishes CI-built wheels, not developer-machine sdists.

Run the Docker end-to-end packaging test:

```bash
bash e2e/run.sh
```

That test builds a local wheel, installs it from `/tmp` into a clean Python
runtime image with no Go toolchain, and scans fake fixture secrets. An Alpine
canary also exists at `bash e2e/run-alpine.sh`; it currently documents the known
musl `ctypes`/Go `c-shared` loader blocker.

## Security And Supply Chain

PyBetterleaks is security tooling, so the release path should be strict:

- Betterleaks is pinned in `bridge/go.mod`
- the bundled Betterleaks pin is documented in `docs/betterleaks-pin.md`
- CI checks that `go.mod`, `go.sum`, and the bridge version constant agree
- wheels are built in GitHub Actions
- PyPI publication uses trusted publishing
- runtime installs never download native binaries
- wheel smoke tests import the package and run the native bridge
- Docker E2E installs a locally built wheel into a no-Go runtime image

## Benchmarks

Benchmark numbers are intentionally not listed yet. The first real release
should include measured comparisons against:

- direct Betterleaks CLI invocation
- Python `subprocess` wrapper overhead
- native PyBetterleaks bridge calls

No fake charts. The scanner deserves better.
