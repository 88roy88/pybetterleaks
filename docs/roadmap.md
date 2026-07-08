# Roadmap

## v0.1

- `scan_text`
- `scan_dir`
- `betterleaks_version`
- Typed dataclass results
- Self-contained platform wheels
- GitHub Actions wheel builds

## v0.2

- Typed `BetterleaksConfig`, `Rule`, `Extend`, `Expr`, and `RequiredRule`
  dataclasses.
- Programmatic config serialization for `scan_text` and `scan_dir`.
- Async `scan_text_async` and `scan_dir_async` wrappers with native
  cooperative cancellation.
- Validation env var bridging for Betterleaks Expr validators.
- Native scan tests against a curated fake-secret fixture suite.
- Reproducible synthetic benchmarks with an optional Betterleaks CLI baseline.
- Release artifact checksums.
- Better wheel smoke coverage for typed config and async.
- Musllinux/Alpine investigation and canary. Official wheels are unsupported in
  v0.2 and remain blocked by the current Go/musl `initial-exec TLS` loader
  failure.

See [v0.2 plan](v0.2-plan.md) for implementation details and acceptance
criteria.

## v0.3

- Git repository scan mode for local repository workflows.
- Streaming scan result API for large scans.
- Config coverage expansion for stable Betterleaks TOML fields.
- Release hardening: API guides, benchmark artifacts, release templates, and
  stronger wheel smoke coverage.

See [v0.3 plan](v0.3-plan.md) for implementation details and open decisions.

## Later

- GitHub/GitLab/Hugging Face/S3 source wrappers.
- Linux arm64 wheels if demand and CI capacity justify them.
- SBOM generation.
- Artifact signing.
- Published benchmark tables against Betterleaks CLI and subprocess wrappers.
