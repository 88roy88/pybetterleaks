# Getting Started

## Install

```bash
pip install pybetterleaks
```

For production Docker images, prefer binary-only installs:

```bash
pip install --only-binary=:all: pybetterleaks
```

## Local Repository Build

Build the native bridge locally:

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

The example secret is synthetic.

## Typed Config

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

Use `config_path=".betterleaks.toml"` when you already have a TOML config file.
Do not pass both `config` and `config_path`.

## Directory Scans

```python
from pybetterleaks import scan_dir

result = scan_dir(".", config_path=".betterleaks.toml")

if result.ok:
    for finding in result.findings:
        print(f"{finding.file}:{finding.line} {finding.rule_id}")
else:
    for error in result.errors:
        print(f"{error.code}: {error.message}")
```

Services that prefer exception-style control flow can opt in per call:

```python
from pybetterleaks import ScanFailedError, scan_dir

try:
    result = scan_dir(".", config_path=".betterleaks.toml", raise_on_error=True)
except ScanFailedError as exc:
    print(exc.code, exc.errors)
```

## Git Worktree Scans

```python
from pybetterleaks import SUPPORTED_GIT_SCOPES, scan_git

print(SUPPORTED_GIT_SCOPES)
result = scan_git(".", scope="worktree", config_path=".betterleaks.toml")

for finding in result.findings:
    print(f"{finding.file}:{finding.line} {finding.rule_id}")
```

`scan_git` currently supports local worktree scans only. It validates that the
target is inside a Git worktree, skips `.git` metadata, and does not invoke the
Git executable. See [Git Scanning](git-scanning.md) for scope details and
deferred Git modes.

## Async Scans

```python
import asyncio
from pybetterleaks import scan_git_async

async def main() -> None:
    result = await scan_git_async(".", timeout_seconds=10)
    print(result.ok, len(result.findings))

asyncio.run(main())
```

The async API uses an executor under the hood. When the Python task is
cancelled, PyBetterleaks sends a cancellation request to the Go bridge for the
active scan request id.

## Docker

```dockerfile
FROM python:3.12-slim

RUN pip install --only-binary=:all: pybetterleaks

COPY . /app
WORKDIR /app

CMD ["python", "scan.py"]
```

No `go install`, no Betterleaks CLI, and no install-time native binary download.

## Build The Docs

```bash
uv run --group docs mkdocs serve
```

The published HTML site is built by GitHub Actions from the public Markdown
files configured in `mkdocs.yml`.
