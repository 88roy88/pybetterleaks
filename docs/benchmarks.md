# Benchmarks

This page records the current PyBetterleaks benchmark results and the commands
used to reproduce them. The numbers are synthetic and local, but they are useful
as a baseline for release checks and future performance work.

## Current Results

Measured on 2026-07-09 from the local v0.2 working tree after inline typed
config support.

| Field | Value |
| --- | --- |
| OS | macOS 15.0.1 arm64 |
| Python | CPython 3.13.9 |
| Go | go1.26.5 darwin/arm64 |
| Bundled Betterleaks | v1.6.1 |
| Betterleaks CLI | Homebrew `betterleaks` 1.6.1 at `/opt/homebrew/bin/betterleaks` |
| Native mode | bundled Go shared library through `ctypes` |
| CLI baseline | included for directory scans |

### Synthetic Rule

The benchmark uses a typed config with one custom rule:

```python
Rule(
    id="pybetterleaks-bench",
    description="Synthetic PyBetterleaks benchmark rule",
    regex=r"PYBETTERLEAKS_BENCH_[A-Z0-9]{16}",
    keywords=["PYBETTERLEAKS_BENCH_"],
)
```

The fixture secret is `PYBETTERLEAKS_BENCH_0123456789ABCDEF`.

### Results Table

| Command | Fixture | Warmups | Rounds | Mean | Median | Min | Max |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `scan_text` | one synthetic secret | 5 | 30 | 0.16 ms | 0.16 ms | 0.06 ms | 0.30 ms |
| `scan_dir` | 50 files, 2 secrets per file | 5 | 30 | 1.96 ms | 2.00 ms | 1.51 ms | 2.43 ms |
| `betterleaks dir` | 50 files, 2 secrets per file | 5 | 30 | 27.99 ms | 24.82 ms | 21.78 ms | 79.98 ms |
| `scan_text` | one synthetic secret | 3 | 20 | 0.18 ms | 0.17 ms | 0.07 ms | 0.40 ms |
| `scan_dir` | 500 files, 2 secrets per file | 3 | 20 | 16.73 ms | 16.66 ms | 15.85 ms | 18.88 ms |
| `betterleaks dir` | 500 files, 2 secrets per file | 3 | 20 | 29.84 ms | 29.83 ms | 26.95 ms | 35.35 ms |

## Reproduce

Build the native bridge before running benchmarks:

```bash
uv sync --all-extras --dev
uv run python scripts/build_native.py
```

Run the same benchmark cases, including the Betterleaks CLI baseline:

```bash
brew install betterleaks
uv run python benchmarks/bench.py \
  --cli \
  --subprocess-wrapper \
  --rounds 30 \
  --warmups 5 \
  --files 50 \
  --secrets-per-file 2 \
  --json-output benchmark-results/local-50.json \
  --markdown-output benchmark-results/local-50.md

uv run python benchmarks/bench.py \
  --cli \
  --subprocess-wrapper \
  --rounds 20 \
  --warmups 3 \
  --files 500 \
  --secrets-per-file 2 \
  --json-output benchmark-results/local-500.json \
  --markdown-output benchmark-results/local-500.md
```

Expected output shape:

```text
files=50 secrets_per_file=2
warmups=5 rounds=30
pybetterleaks.scan_text: mean=0.16ms median=0.16ms min=0.06ms max=0.30ms
pybetterleaks.scan_dir: mean=1.96ms median=2.00ms min=1.51ms max=2.43ms
betterleaks cli dir: mean=27.99ms median=24.82ms min=21.78ms max=79.98ms
```

To use a specific CLI binary instead of the one on `PATH`, pass `--cli-path`:

```bash
uv run python benchmarks/bench.py --cli --cli-path /path/to/betterleaks
```

CI runs a smaller benchmark and uploads JSON/Markdown artifacts from
`benchmark-results/`. It also builds a local wheel and runs a tiny
wheel-installed benchmark smoke test from a temporary virtual environment.

## How To Read These Numbers

These results should be read as SDK integration measurements, not as proof that
PyBetterleaks makes the Betterleaks engine itself faster.

PyBetterleaks runs inside the already-started Python process:

```text
Python process
  -> ctypes call into already-loaded Go shared library
  -> Betterleaks scan
  -> JSON response
  -> Python dataclasses
```

The CLI baseline starts a new process for each measured scan:

```text
Python benchmark process
  -> subprocess starts betterleaks
  -> CLI parses args and config
  -> Betterleaks scan
  -> CLI writes output
  -> process exits
```

For small scans, CLI startup and command setup are a large share of total time.
That is the core PyBetterleaks use case: Python services, CI helpers, notebooks,
agent tools, and repeated scans that should call an importable SDK instead of
spawning a fresh command each time.

`scan_text` mostly measures Python-to-native boundary overhead, request JSON
serialization, config handoff, Betterleaks setup, and result parsing for one
small input.

`scan_dir` is the more useful SDK-level benchmark. It covers fixture creation
outside the measured path, then measures scanning a directory with synthetic
files and parsing the returned JSON into typed Python dataclasses.

`betterleaks dir` is the upstream CLI baseline. It includes process startup and
CLI output generation, but it does not include Python JSON parsing or dataclass
construction. On this run the SDK is faster for both measured directory cases,
largely because the benchmark makes repeated warm calls from an already-started
Python process into an already-loaded native library.

The 50-file CLI max includes a local outlier. Prefer medians when comparing
these small, sub-100ms command timings.

The earlier 500-file benchmark exposed a separate SDK bug: when callers used a
typed `BetterleaksConfig`, PyBetterleaks generated the TOML config inside a
brand-new temporary directory for every scan. Profiling showed that path was
much slower than scanning with a stable `config_path`. The SDK now sends typed
configs as inline TOML over the JSON ABI and the Go bridge parses them directly
with Betterleaks' config parser.

As scan work grows, PyBetterleaks still pays real costs for Go-to-C JSON
serialization, crossing the C ABI boundary, Python JSON parsing, and dataclass
construction. Keep using these numbers as a release baseline, not as a universal
claim about all repositories or all rule sets.

These numbers are not a security-engine benchmark and should not be presented
as a universal Betterleaks performance claim. They are a PyBetterleaks release
baseline: the public API stays importable, the bundled bridge stays fast enough
for CI and service use, and future changes have a simple regression check.

## Next Measurements

- Add cold-start versus warm-call measurements.
- Add larger repository-shaped fixtures with mixed file types.
- Track results across supported wheel platforms once the data is stable.
