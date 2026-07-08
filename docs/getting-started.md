# Getting Started

## Install

After the first wheel release is published:

```bash
pip install pybetterleaks
```

For production Docker images, prefer binary-only installs:

```bash
pip install --only-binary=:all: pybetterleaks
```

## Local Repository Build

Until the first PyPI release is published, build the native library locally:

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

The example secret is intentionally fake.

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

The published HTML site is built by GitHub Actions from the Markdown files in
`docs/`.
