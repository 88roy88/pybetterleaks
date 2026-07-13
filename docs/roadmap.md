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
- Musllinux/Alpine investigation. Official wheels are unsupported and remain
  blocked by the current Go/musl `initial-exec TLS` loader failure.

See [v0.2 plan](v0.2-plan.md) for implementation details and acceptance
criteria.

## v0.3

- Git worktree scan mode for local repository workflows, with tracked/staged
  scopes planned only if they can preserve the no-runtime-subprocess promise.
- Release hardening: PyPI trusted publishing, post-publish PyPI smoke tests,
  v1 readiness docs, benchmark docs, and stronger wheel smoke coverage.

See [v0.3 plan](v0.3-plan.md) for implementation details and open decisions.

## v0.4

- Config ergonomics:
  - `Expr.min_entropy(...)`
  - `Expr.token_efficiency(...)`
  - allowlist-replacement helpers such as `Expr.path_matches_any(...)`,
    `Expr.git_commit_in(...)`, and `Expr.finding_contains_any(...)`
  - expression composition helpers: `Expr.any_of(...)`, `Expr.all_of(...)`,
    and `Expr.not_(...)`
  - `Validation.valid(...)`, `Validation.invalid(...)`,
    `Validation.unknown(...)`, `Validation.needs_validation(...)`, and
    `Validation.bearer_get(...)`
  - `Rule.regex_rule(...)`
  - `Rule.path_rule(...)`
  - `Rule.prefixed_token_rule(...)`
  - `Rule.pem_private_key_rule(...)`
  - `Rule.entropy` compatibility serialization
- Relative `extend.path` handling for inline configs through
  `extend_base_path`.
- Async cancellation hardening so cancelled Python tasks shield and drain the
  executor future after requesting native cancellation.
- Roadmap/backlog cleanup now that config coverage for Betterleaks `v1.6.1`
  stable fields is closed.

See [v0.4 plan](v0.4-plan.md) for implementation details and acceptance
criteria.

## v0.5

- Release artifact inspection before wheel upload and again before PyPI
  publishing.
- Checksum verification after `SHA256SUMS` generation.
- GitHub release notes generated from tags with `SHA256SUMS` attached.
- GitHub artifact attestations for wheels and checksums.
- Documented supply-chain story, deprecation policy, and SBOM decision.

See [v0.5 plan](v0.5-plan.md) for implementation details and acceptance
criteria.

## v0.6

- Release branch workflow for `release/*`.
- Version automation that defaults to patch bumps unless maintainers choose a
  different release level.
- Post-release audit automation for PyPI, GitHub release assets, checksums, and
  install smoke tests.
- GitHub Actions maintenance, including Node deprecation cleanup where possible.
- CI benchmark artifacts and wheel-installed benchmark smoke tests.
- Project hygiene files: issue templates, PR template, and `SECURITY.md`.
- README visual polish and dedicated Git scanning docs.

See [v0.6 plan](v0.6-plan.md) for implementation details and open decisions.

## Later

- Streaming scan result APIs for very large scans.
- GitHub/GitLab/Hugging Face/S3 source wrappers.
- Linux arm64 wheels if demand and CI capacity justify them.
- SBOM generation.
- Artifact signing.
- Published benchmark tables against Betterleaks CLI and subprocess wrappers.
