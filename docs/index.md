# PyBetterleaks

Python-native Betterleaks. No CLI wrapper, no Go toolchain in production
images, and no runtime `subprocess`.

```bash
pip install pybetterleaks
```

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
for finding in result.findings:
    print(f"{finding.rule_id}: {finding.secret}")
```

PyBetterleaks wraps the Betterleaks Go engine through a tiny `ctypes` JSON ABI
and returns typed Python dataclasses. It is built for CI jobs, Python services,
agent tools, notebooks, and Docker images that should stay simple.

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

## What It Supports Today

- typed config dataclasses
- config helpers for filters, validation results, common rules, and relative
  `extend.path` handling
- async scan wrappers with cooperative native cancellation
- local Git worktree scans
- validation env var bridging
- self-contained platform wheels
- bundled Betterleaks `v1.6.1`
- release artifact checksums
- release artifact inspection and provenance attestations
- Docker packaging E2E
- no runtime binary downloads
- no runtime Betterleaks CLI dependency

Musllinux/Alpine remains a documented loader blocker for the current Go shared
library design.

## Start Here

- [Getting Started](getting-started.md)
- [Configuration](configuration.md)
- [Git Scanning](git-scanning.md)
- [API Reference](api.md)
- [Benchmarks](benchmarks.md)
- [Troubleshooting](troubleshooting.md)
- [Supply Chain](supply-chain.md)
