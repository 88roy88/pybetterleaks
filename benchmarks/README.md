# PyBetterleaks Benchmarks

These benchmarks are maintainer tools, not runtime package code. They generate
synthetic fixtures at runtime so the repository never stores realistic-looking
secrets.

Run the PyBetterleaks-only benchmark:

```bash
uv run python benchmarks/bench.py
```

Optionally compare against a local Betterleaks CLI binary:

```bash
uv run python benchmarks/bench.py --cli --cli-path /path/to/betterleaks
```

Use the output as a release input, not as marketing copy. README benchmark
claims should only be updated from a named machine/runner and a committed
benchmark command.
