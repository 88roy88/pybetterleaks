# PyBetterleaks

Python-native Betterleaks. No CLI dance, no Go toolchain in production images,
and no runtime `subprocess`.

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

PyBetterleaks wraps the Betterleaks Go engine through a tiny `ctypes` JSON ABI
and returns typed Python dataclasses. It is built for CI jobs, Python services,
agent tools, notebooks, and Docker images that should stay boring.

## Why It Exists

Betterleaks is fast and serious. Python is everywhere. The awkward bit is the
boundary between them.

Shelling out works until process output becomes your SDK contract. PyBetterleaks
keeps the engine native and gives Python a clean importable API.

```text
Python app
  -> pybetterleaks
    -> ctypes JSON ABI
      -> bundled Go shared library
        -> Betterleaks
```

## What v0.1 Ships

- `scan_text` and `scan_dir`
- typed dataclass results
- self-contained platform wheels
- bundled Betterleaks `v1.6.1`
- GitHub Actions wheel builds
- no runtime binary downloads
- no runtime Betterleaks CLI dependency

## Start Here

- [Getting Started](getting-started.md)
- [API Reference](api.md)
- [Architecture](architecture.md)
- [Release Checklist](release-checklist.md)
