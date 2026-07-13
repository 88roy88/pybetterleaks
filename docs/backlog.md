# Backlog

This backlog is the project-wide parking lot for everything discussed but not
fully shipped, plus decisions that should stay visible for future maintainers.

## Current Baseline

Already implemented:

- `scan_text`
- `scan_dir`
- `scan_git(..., scope="worktree")`
- `scan_text_async`, `scan_dir_async`, and `scan_git_async`
- cooperative native cancellation by request id
- typed dataclass models for findings, errors, and results
- typed `BetterleaksConfig`, `Rule`, `Extend`, `Expr`, and `RequiredRule`
- config ergonomics: namespaced `Expr` filter helpers, `Validation` helpers,
  common `Rule` constructors, and relative `extend.path` handling
- `Rule.entropy` compatibility serialization
- inline TOML config handoff through `config_toml`
- `py.typed`
- bundled Go shared library loaded with `ctypes`
- no runtime Betterleaks CLI calls
- no runtime `subprocess` for supported APIs
- uv-managed Python environment
- MkDocs Material documentation site with generated API reference
- Docker E2E for a glibc Python runtime image
- CI coverage job builds the native bridge so native smoke tests are included
- documented musllinux/Alpine unsupported status
- synthetic benchmarks with optional Betterleaks CLI comparison
- wheel builds for supported non-musl platforms
- release checksum tooling
- release checksum verification
- Betterleaks module checksum pin verification
- wheel artifact inspection in CI and publish workflows
- GitHub release-note generation with `SHA256SUMS` attachment
- GitHub artifact attestations for release wheels and checksums
- manual release preparation workflow for version bump branches
- merge-to-main release tagging for reviewed `release/vX.Y.Z` branches
- `CODEOWNERS` maintainer ownership for protected-branch reviews
- version consistency checker in CI
- post-release audit for PyPI metadata, GitHub release assets, checksums, and
  install smoke checks
- benchmark JSON/Markdown artifacts in CI
- wheel-installed benchmark smoke tests
- issue templates, PR template, and `SECURITY.md`
- README hero visual
- public Git scanning guide
- documented deprecation policy
- documented supply-chain and SBOM decision

## Per-Release Checklist

These are recurring checks before tagging and publishing a new release.

- Push local commits.
- Watch CI, Docs/Pages, E2E, and Wheels.
- Confirm GitHub Pages renders the docs site after push.
- Inspect wheel artifacts for expected platform tags.
- Install built wheels in clean environments.
- Verify `pip install --only-binary=:all: pybetterleaks`.
- Verify Docker install using `python:3.12-slim`.
- Confirm `pybetterleaks/py.typed` ships in wheels.
- Confirm no install-time downloads occur.
- Confirm no musllinux wheels are published.
- Confirm GitHub release notes exist and `SHA256SUMS` is attached.
- Confirm release artifact attestations exist.
- Prepare release notes with:
  - Python package version
  - bundled Betterleaks version `v1.6.1`
  - platform matrix
  - benchmark doc link
  - musllinux/Alpine caveat
- Tag the release only after CI is green.
- Publish to PyPI only with explicit maintainer approval.

## GitHub And Project Admin

- Keep the repository under the intended owner/org.
- Keep `main` protected with required PR review, code-owner review, strict
  up-to-date checks, and required CI contexts.
- Keep auto-delete merged branches enabled.
- Confirm repository topics, description, homepage, and Pages settings.
- Decide whether to add Discussions.
- Decide whether to add funding/sponsor metadata.

## Public API Backlog

### Git Scopes

Current public Git scope:

```python
GitScope = Literal["worktree"]
SUPPORTED_GIT_SCOPES = ("worktree",)
```

Unsupported scopes:

- `tracked`: scan only files tracked by Git.
- `staged`: scan staged changes only.
- `diff`: scan a commit range or ref pair.
- `history`: scan commit history.

Why unsupported:

- Upstream Betterleaks' Git history and diff source shells out to the `git`
  executable.
- PyBetterleaks keeps a no-runtime-subprocess promise for supported APIs.
- These scopes need either a pure-Go Git implementation or an explicit product
  decision to allow a subprocess-backed optional mode.

Open decisions:

- Should `scan_git` keep defaulting to `worktree` once more scopes exist?
- Should multiple scopes require an enum-like API instead of strings?
- Is a runtime subprocess ever acceptable for optional history scans?
- Should `tracked` be implemented by pure-Go `.git/index` parsing?

### Streaming Results

Unsupported APIs:

- `iter_scan_text`
- `iter_scan_dir`
- `iter_scan_git`
- `iter_scan_text_async`
- `iter_scan_dir_async`
- `iter_scan_git_async`

Preferred design:

- Use pull-based native scan handles.
- Avoid Python callbacks from Go.
- Add native symbols:
  - `BetterleaksScanStartJSON`
  - `BetterleaksScanNextJSON`
  - `BetterleaksScanClose`
- Close native handles in Python `finally` blocks.
- Use bounded Go channels for backpressure.
- Make cancellation close the native handle and cancel the Go context.

Open decisions:

- Ship sync iterators before async iterators?
- Should collecting APIs eventually use streaming internally?
- What event shape should `ScanNextJSON` return?
- How should partial results and structured errors be surfaced?

### Config Coverage

Status: closed for the reviewed Betterleaks `v1.6.1` stable config surface.

Implemented:

- direct TOML field mapping for supported top-level, `[extend]`, `[[rules]]`,
  and `[[rules.required]]` fields
- namespaced filter helpers:
  - `Expr.min_entropy`
  - `Expr.token_efficiency`
  - `Expr.finding_contains_any`
  - `Expr.finding_matches_any`
  - `Expr.attribute_contains_any`
  - `Expr.attribute_matches_any`
  - `Expr.path_matches_any`
  - `Expr.git_commit_in`
  - `Expr.any_of`, `Expr.all_of`, and `Expr.not_`
- validation helpers:
  - `Validation.valid`
  - `Validation.invalid`
  - `Validation.unknown`
  - `Validation.needs_validation`
  - `Validation.bearer_get`
- rule helpers:
  - `Rule.regex_rule`
  - `Rule.path_rule`
  - `Rule.prefixed_token_rule`
  - `Rule.pem_private_key_rule`
- `Rule.entropy` as a compatibility field
- relative `extend.path` resolution through `extend_base_path` and
  `BetterleaksConfig.write(...)`
- native smoke coverage that proves helper-generated configs are accepted by
  the bundled Betterleaks bridge

Deliberately unsupported:

- legacy global/per-rule `allowlists` dataclasses; use modern Expr filters
- archive/decode/file-size tuning fields until upstream exposes stable config
  fields for them
- provider-specific validation presets until real user demand appears

Future rule for config additions:

- Re-read upstream Betterleaks config docs and code before adding fields.
- Every added field must serialize to Betterleaks-compatible TOML.
- Native smoke tests must prove Betterleaks accepts generated TOML.
- Docs must map Python field names to TOML spellings.
- Invalid combinations should fail in Python where practical.

### Provider And Remote Scans

Unsupported source wrappers:

- GitHub URL scans
- GitLab URL scans
- Hugging Face scans
- S3 scans
- arbitrary remote Git URL scans

Reasons to defer:

- Authentication and token handling need careful API design.
- Provider pagination and rate limits need tests.
- Network behavior changes the trust and runtime story.
- Local Git and streaming should stabilize first.

## Native Bridge Backlog

- Keep the C symbol surface small and stable.
- Preserve JSON as the ABI boundary.
- Add streaming handle symbols only after lifecycle design is settled.
- Add more native unit tests around request validation.
- Consider response-size and memory-pressure tests for large findings sets.
- Consider chunked or streaming response paths for large scans.
- Keep panic recovery and structured errors for all exported symbols.
- Keep `BetterleaksFree` ownership rules documented and tested.

## Platform And Wheel Backlog

Supported targets:

- manylinux x86_64
- macOS arm64
- macOS x86_64
- Windows amd64

Future platform tasks:

- Linux arm64 wheels if CI capacity and demand justify them.
- Confirm wheel tags are never `py3-none-any`.
- Keep sdists disabled or clearly source-build-only.

Unsupported:

- Alpine/musllinux wheels

Tracking issue:

- <https://github.com/roymezan/pybetterleaks/issues/1>

Current musllinux blocker:

```text
initial-exec TLS resolves to dynamic definition
```

Notes:

- This is a Go + musl shared-library loader limitation seen when Python loads
  the Go shared library through `ctypes`.
- Building the Go shared library on Alpine with `CGO_ENABLED=1` and
  `-buildmode=c-shared` does not fix runtime `dlopen`.
- `-linkmode=external` did not fix the loader failure.
- `LD_PRELOAD` is not acceptable for release; it also segfaulted locally.
- Static `CGO_ENABLED=0` Go builds are useful for executables, not for the
  current `ctypes` shared-library design.

Possible future choices:

- Wait for upstream Go/musl shared-library TLS improvements.
- Keep Alpine unsupported indefinitely.
- Add a musllinux-only sidecar worker executable, but that weakens the current
  no-runtime-subprocess promise and requires an explicit product decision.

## CI/CD Backlog

- Keep GitHub Actions caching for:
  - uv cache
  - Go module cache
  - Go build cache
  - cibuildwheel inputs where practical
- Watch macOS wheel build time; it has been slower than expected.
- Upload benchmark output as CI artifacts.
- Add wheel-installed benchmark smoke tests for Linux and macOS.
- Keep post-publish PyPI smoke tests running from a temporary virtual
  environment.
- Keep `CIBW_SKIP: "*-musllinux_*"` until Alpine is genuinely supported.
- Confirm publish workflow uses trusted publishing only.
- Do not store a PyPI token.

## Benchmarks And Performance Backlog

Already learned:

- SDK wins small repeated scans because it avoids CLI process startup.
- Inline typed config is faster and cleaner than temp TOML files.
- The old 500-file slowdown came from creating a fresh temp config directory.
- `scan_dir` currently performs well against the CLI on local synthetic tests.

Future benchmark tasks:

- Add cold-start versus warm-call measurements.
- Add repository-shaped fixtures with mixed file types.
- Add wheel-installed benchmarks from clean virtual environments.
- Track benchmark results by platform in CI artifacts.
- Compare against:
  - Betterleaks CLI
  - subprocess wrapper baseline
  - previous PyBetterleaks releases
- Add pprof/flamegraph guidance for bridge profiling.
- Avoid broad performance claims beyond the measured scenarios.

## Documentation Backlog

- Keep the README punchy and "developer viral", but honest.
- Add a dedicated Git scanning guide.
- Add a streaming guide once iterators exist.
- Expand generated API docs with examples for every public function.
- Keep every README command tested or marked illustrative.
- Add wheel/platform troubleshooting page if install questions grow.
- Keep `docs/backlog.md` updated after each design decision.

## Supply Chain And Release Trust

Current baseline:

- Release checksums are generated and verified.
- `SHA256SUMS` is attached to GitHub releases.
- GitHub artifact attestations cover release wheels and checksums.
- PyPI trusted publishing is tokenless.
- Wheel artifacts are inspected before upload and before publish.
- The bundled Betterleaks module and `go.mod` checksums are verified against
  expected values before release.

Future tasks:

- SBOM generation before `1.0.0` or before publishing sdists.
- Artifact signing beyond GitHub artifact attestations if users need it.
- Document bundled Betterleaks version in every release note.
- Re-run full Python, Go, wheel, and Docker E2E gates before tags.

## Betterleaks Coupling

Current decision:

- Strongly couple through `bridge/go.mod` and `go.sum`.
- Do not add Betterleaks as a Git submodule for now.
- Do not use a Go `replace` directive in release builds.

Future tasks:

- Revisit a local-only `replace` workflow if frequent Betterleaks upstream
  development makes it useful.
- Keep the bundled Betterleaks version exposed through
  `betterleaks_version()`.
- Keep Python package version separate from Betterleaks version.
- Document Betterleaks upgrades in `docs/betterleaks-pin.md`.
- Re-run config-doc review before adding config fields.

## Source Distribution Policy

Current decision:

- Publish wheels first.
- Do not publish sdists until source builds have a documented Go story.

Future tasks:

- Decide whether sdists should require Go.
- Decide whether sdists should fail loudly when Go is missing.
- Ensure generated native libraries never accidentally land in source archives.

## Long-Term Ideas

- Native streaming for very large scans.
- Rich Git history and diff scans without runtime subprocesses.
- Provider wrappers for GitHub, GitLab, Hugging Face, and S3.
- Linux arm64 wheels.
- Alpine sidecar worker only if the no-subprocess promise changes.
- Provider-specific validation presets.
- SBOM generation and optional artifact signing as release defaults.
- Public benchmark dashboard.
- More polished website and examples.

## Decisions Needed

- Is the no-runtime-subprocess promise absolute for every future feature?
- Should Git history scans wait for pure-Go implementation, or be optional and
  subprocess-backed?
- Should Alpine remain unsupported, or should sidecar-worker mode be allowed?
- Should `scan_git` default stay `worktree` after more scopes exist?
- Which future upstream config fields are worth modeling before users request
  them?
- Should SBOM generation be required before `1.0.0`, or only when sdists are
  supported?
- Should release versioning stay Python-native (`0.x.y`) rather than matching
  Betterleaks (`1.6.1`)?
