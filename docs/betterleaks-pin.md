# Betterleaks Pin

PyBetterleaks intentionally couples each release to one explicit Betterleaks
release. The Python package is not a loose plugin layer; it ships a native
library built against the Betterleaks Go packages named here.

## Current Pin

- Module: `github.com/betterleaks/betterleaks`
- Version: `v1.6.1`
- Tag URL: <https://github.com/betterleaks/betterleaks/releases/tag/v1.6.1>
- Source URL: <https://github.com/betterleaks/betterleaks/tree/v1.6.1>
- Checksum source: `bridge/go.sum`
- Module checksum: `h1:ZSnqAMwvIudpeHxzbBu8LlAwV/T8Ty2ygrJDtC4IBiQ=`
- `go.mod` checksum: `h1:VxY1tDWcVg0+WNrzM+Qng8zJq7Np5zXAkxOc0/LxCAE=`
- Runtime version constant: `bridge/bridge.go`

The pin is enforced by:

```bash
uv run python scripts/check_betterleaks_pin.py
```

That check verifies all of the following:

- `bridge/go.mod` requires `github.com/betterleaks/betterleaks v1.6.1`.
- `bridge/go.sum` contains the expected checksums for the pinned module and
  its `go.mod`.
- `bridge/bridge.go` reports the same bundled version through
  `betterleaks_version()`.

## Why Not A Git Submodule?

A submodule would make the upstream source visible in the checkout, but Go would
not use it unless the bridge added a `replace` directive. Keeping both a
submodule and a normal module dependency creates two pins that can drift.

For v0.2, the release source of truth is the Go module pin plus `go.sum`
checksums. This keeps CI, local builds, and wheel builds aligned with Go's
normal reproducible dependency flow.

Use a submodule only if PyBetterleaks needs to carry an unreleased Betterleaks
patch or build from a maintained fork. In that case, add a `replace` directive,
document the fork commit, and make CI require `actions/checkout` with
submodules enabled.

## Upgrade Checklist

1. Update `bridge/go.mod` to the new Betterleaks tag.
2. Run `go mod tidy` in `bridge/`.
3. Update `bundledBetterleaksVersion` in `bridge/bridge.go`.
4. Update `EXPECTED_BETTERLEAKS_CHECKSUMS` in
   `scripts/check_betterleaks_pin.py` with the new `go.sum` values.
5. Update this document and the README if the bundled version is mentioned.
6. Run `uv run python scripts/check_betterleaks_pin.py`.
7. Run the full Python, Go, wheel, and Docker E2E checks before release.
