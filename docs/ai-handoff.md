# AI Handoff

This file is for future AI agents and human maintainers. It compresses the
research and decisions made so far.

## User Intent

The user wants a Python integration for Betterleaks. They explicitly do not want
a package that shells out with `subprocess` or `popen` at runtime. They want a
self-contained PyPI package that is easy to use in Docker and can be built by CI
for multiple platforms.

## Current Repository State

As of 2026-07-09:

- Workspace: `/Users/roymezan/Documents/BetterLeaksPython`
- Git branch: `main`
- Remote: `https://github.com/roymezan/pybetterleaks.git`
- Python package/import name: `pybetterleaks`
- Python package version in development: `0.6.0`
- Bundled Betterleaks version: `v1.6.1`
- Local Go observed after installation: `go1.26.5 darwin/arm64`
- Python SDK, Go bridge, tests, Docker E2E, CI workflows, docs, typed config,
  async wrappers, benchmarks, release artifact inspection, provenance
  attestations, and checksum tooling are present.

## Technical Path

PyBetterleaks bundles a Go shared library bridge:

```text
Python package
  -> ctypes JSON ABI
    -> Go shared library built with -buildmode=c-shared
      -> Betterleaks Go packages
```

Runtime subprocesses are rejected. Build-time subprocesses in scripts and CI are
allowed.

The exported ABI is:

- `BetterleaksScanJSON`
- `BetterleaksCancel`
- `BetterleaksFree`
- `BetterleaksVersion`

All scan requests and responses cross the ABI as UTF-8 JSON.

## Betterleaks Config Coupling

Before planning v0.2, upstream Betterleaks config docs were read at
`betterleaks/docs/config.md`. The important conclusion: PyBetterleaks should
model Betterleaks TOML directly instead of inventing a Python-only rules
language.

Modern Betterleaks config uses:

- `prefilter`
- `filter`
- `validate`
- `[extend]`
- `[[rules]]`
- `[[rules.required]]`

Legacy allowlists are intentionally not modeled. Use Expr filters and
prefilters instead. v0.4 closes the planned Betterleaks `v1.6.1` config-helper
work by adding namespaced filter helpers, validation result helpers, common rule
constructors, relative `extend.path` resolution, and `Rule.entropy` only as a
compatibility field.

## v0.2 Decisions

- Add `BetterleaksConfig`, `Rule`, `Extend`, `Expr`, and `RequiredRule`.
- Keep dataclasses and no runtime dependencies.
- Serialize typed configs to TOML strings and pass `config_toml` through the
  JSON ABI. The Go bridge parses inline TOML with Betterleaks'
  `config.ParseTOMLString`.
- Add `scan_text_async` and `scan_dir_async`.
- Implement async cancellation through request ids plus `BetterleaksCancel`.
- Add `validation_env_vars` and mirror only explicitly allowlisted values into
  Go env during validation scans.
- Lock validation-env scans so one scan cannot observe another scan's temporary
  env overlay.
- Add synthetic benchmarks under `benchmarks/`.
- Add release checksum generation.
- Keep musllinux/Alpine documented as unsupported for the current Go shared
  library design.

## Musllinux Finding

Alpine experiments failed when Python loaded the Go shared library through
`ctypes`:

```text
initial-exec TLS resolves to dynamic definition
```

This was also reproduced by building Betterleaks with Go `-buildmode=c-archive`
and linking that archive into a musl shared object. It produced the same loader
error. Do not publish musllinux wheels until this is solved without `LD_PRELOAD`,
wrapper launchers, or runtime subprocesses.

## Important Constraints

- Use `apply_patch` for manual file edits in this environment.
- Do not revert user changes.
- Do not publish to PyPI without explicit user approval.
- Do not run destructive Git commands.
- The user explicitly asked to stop committing/pushing without permission. For
  this v0.2 implementation, they later gave permission to commit and push when
  done.
- Network is restricted in this environment. If dependency fetching is required
  and sandboxed commands fail due to network, request escalation.

## Useful Commands

```bash
uv sync --all-extras --dev
uv run python scripts/build_native.py
uv run coverage run -m pytest
uv run coverage report
uv run ruff check .
uv run mypy python
GOCACHE=/private/tmp/go-cache-pybetterleaks go test ./...
GOCACHE=/private/tmp/go-cache-pybetterleaks go vet ./...
uv run --group docs mkdocs build --strict
uv run python benchmarks/bench.py --rounds 1 --warmups 0
uv build --wheel
uv run python scripts/inspect_wheels.py dist
uv run python scripts/checksums.py dist --output ../release/SHA256SUMS
uv run python scripts/checksums.py dist --verify ../release/SHA256SUMS
uv run python scripts/wheel_smoke.py
bash e2e/run.sh
```

Use `uv build --sdist` only to inspect the source archive. It should not contain
generated native libraries, and sdists should not be published until source
builds are explicitly supported.

## References

- Shared planning chat:
  <https://chatgpt.com/share/6a4e9907-1608-83eb-81e0-c92a48eb8a7a>
- Betterleaks repository:
  <https://github.com/betterleaks/betterleaks>
- Betterleaks config docs:
  <https://github.com/betterleaks/betterleaks/blob/main/docs/config.md>
- Go build modes:
  <https://pkg.go.dev/cmd/go#hdr-Build_modes>
- cibuildwheel:
  <https://cibuildwheel.pypa.io/en/stable/>
