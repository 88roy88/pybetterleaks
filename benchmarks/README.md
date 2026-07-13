# PyBetterleaks Benchmarks

These benchmarks are maintainer tools, not runtime package code. They generate
synthetic fixtures at runtime so the repository never stores realistic-looking
secrets.

Run the PyBetterleaks-only benchmark:

```bash
uv run python benchmarks/bench.py
```

Write benchmark artifacts:

```bash
uv run python benchmarks/bench.py \
  --subprocess-wrapper \
  --json-output benchmark-results/benchmark.json \
  --markdown-output benchmark-results/benchmark.md
```

Optionally compare against a local Betterleaks CLI binary:

```bash
uv run python benchmarks/bench.py --cli --cli-path /path/to/betterleaks
```

Run a tiny clean-wheel benchmark smoke after building a local wheel:

```bash
uv build --wheel --out-dir wheelhouse
uv run python scripts/wheel_benchmark_smoke.py --wheel wheelhouse
```

Use the output as a release input, not as marketing copy. README benchmark
claims should only be updated from a named machine/runner and a committed
benchmark command.
