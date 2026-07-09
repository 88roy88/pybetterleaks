# v1.0 Readiness

PyBetterleaks should reach `1.0.0` when the core promise is stable and
repeatable, not when every possible Betterleaks feature has a Python wrapper.

## Release Meaning

`1.0.0` should mean:

- the supported public API is stable
- platform wheels publish reliably
- users can install without Go, the Betterleaks CLI, or runtime downloads
- common failure modes are documented and tested
- future breaking changes have a deprecation policy

## Required For v1.0

Public API stability:

- `scan_text`, `scan_dir`, and `scan_git`
- `scan_text_async`, `scan_dir_async`, and `scan_git_async`
- `BetterleaksConfig`, `Rule`, `Expr`, `Extend`, and `RequiredRule`
- `Finding`, `ScanError`, and `ScanResult`
- `GitScope = Literal["worktree"]`
- documented deprecation policy

Packaging and release reliability:

- PyPI wheels publish cleanly from a tag
- Linux x86_64, macOS arm64, macOS x86_64, and Windows amd64 wheels install and
  pass smoke tests
- `pip install --only-binary=:all: pybetterleaks` works
- no install-time binary downloads
- no runtime Betterleaks CLI or Go toolchain dependency
- no sdists unless source builds have an explicit Go build story

CI/CD:

- CI, Wheels, E2E, Docs, and Publish workflows are consistently green
- published wheels are verified from PyPI in a temporary virtual environment
- release checksums are generated and retained
- GitHub release notes are templated or generated
- PyPI trusted publishing stays tokenless

Docs:

- README has current status and platform support
- Getting Started is copy-pasteable
- configuration guide covers the supported typed config surface
- Git scanning guide documents `worktree` scope and unsupported scopes
- async/cancellation guide documents best-effort cancellation
- platform page documents musllinux/Alpine as unsupported
- API reference is generated and current
- troubleshooting covers native loader and install failures

Testing:

- Python unit tests cover request serialization and model parsing
- native smoke tests cover text, directory, Git worktree, structured errors, and
  timeouts
- Docker E2E installs a locally built wheel into a no-Go runtime image
- wheel smoke tests run across every release wheel
- PyPI smoke tests install the published wheel and exercise native APIs
- cancellation tests prove the expected cooperative behavior

Security and supply chain:

- bundled Betterleaks version is pinned and documented
- release notes state the bundled Betterleaks version
- validation env var behavior is documented
- fixtures are synthetic and non-operational
- checksums are published
- SBOM and provenance are either implemented or explicitly deferred with an
  owner decision

## Not Required For v1.0

These should not block `1.0.0`:

- musllinux/Alpine wheels
- Git history, diff, tracked-only, or staged-only scans
- GitHub, GitLab, Hugging Face, or S3 source wrappers
- streaming scan results
- complete Betterleaks config parity
- Python-version-independent ABI wheels

## Suggested Path

- `0.3.x`: polish README/PyPI text, add post-publish PyPI smoke tests, and close
  obvious release-doc gaps.
- `0.4.0`: release hardening, GitHub release notes, checksum publication,
  artifact inspection, and SBOM/provenance decision.
- `0.5.0`: config/API completeness pass, deprecation policy, and stronger
  cancellation tests.
- `1.0.0rc1`: freeze API and run a full release rehearsal.
- `1.0.0`: publish after the release candidate survives real use.
