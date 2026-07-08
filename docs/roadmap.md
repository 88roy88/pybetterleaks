# Roadmap

## v0.1

- `scan_text`
- `scan_dir`
- `betterleaks_version`
- Typed dataclass results
- Self-contained platform wheels
- GitHub Actions wheel builds

## v0.2

- Typed `BetterleaksConfig` and `Rule` dataclasses.
- Programmatic config serialization for `scan_text` and `scan_dir`.
- Better native bridge coverage of Betterleaks config options without breaking
  the v0.1 JSON ABI.
- Native scan tests against a curated fake-secret fixture suite.
- Reproducible benchmarks against the Betterleaks CLI baseline.
- Linux arm64 wheels if CI capacity permits.
- Release artifact checksums.

See [v0.2 plan](v0.2-plan.md) for the implementation checklist and acceptance
criteria.

## v0.3

- Git repository scan mode.
- Streaming scan result API.
- Async wrapper built on `asyncio.to_thread`.
- Richer validation metadata.

## Later

- GitHub/GitLab/Hugging Face/S3 sources.
- musllinux/Alpine wheels.
- SBOM generation.
- Artifact signing.
- Benchmarks against Betterleaks CLI and subprocess wrappers.
