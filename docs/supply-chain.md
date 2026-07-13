# Supply Chain

PyBetterleaks ships a security scanner as a Python package, so the release
process needs to make the native artifact easy to inspect and hard to publish
accidentally in the wrong shape.

## Release Sources

- Betterleaks is pinned in `bridge/go.mod`.
- Go module checksums are committed in `bridge/go.sum`.
- The bundled Betterleaks version is documented in
  [Betterleaks Pin](betterleaks-pin.md).
- CI checks that the Go module pin, expected `go.sum` checksums, and bridge
  version constant stay aligned.
- Release wheels are built by GitHub Actions, not by a developer laptop.

The Betterleaks pin check verifies exact expected checksums for both the module
archive and its `go.mod` metadata before release:

```bash
uv run python scripts/check_betterleaks_pin.py
```

## Wheel Guarantees

Release wheels should:

- contain `pybetterleaks/py.typed`
- contain exactly one native library in `pybetterleaks/native/`
- omit generated C header files
- be platform wheels, never `py3-none-any`
- never use a musllinux tag while Alpine remains unsupported
- declare `Root-Is-Purelib: false`
- install without downloading native binaries

`scripts/inspect_wheels.py` enforces those checks in the wheel build workflow
and again in the publish workflow.

## Checksums

`scripts/checksums.py` writes SHA256 checksums for release artifacts. The
publish workflow verifies the generated file before publishing and attaches
`SHA256SUMS` to the GitHub release.

Local usage:

```bash
python scripts/checksums.py dist --output ../release/SHA256SUMS
python scripts/checksums.py dist --verify ../release/SHA256SUMS
```

## Trusted Publishing

PyPI publishing uses OpenID Connect trusted publishing. That means the workflow
does not store a PyPI API token. PyPI accepts uploads from the configured GitHub
repository, workflow, environment, and tag event.

## Provenance

The publish workflow creates GitHub artifact attestations for wheels and the
checksum file. These attestations tie artifacts back to the GitHub Actions run
that produced them.

## SBOM Decision

Automated SBOM generation is deferred. The project currently has no runtime
Python dependencies, pins the Go module graph, and publishes wheels only. SBOM
support should be revisited before `1.0.0` or when source distributions become
supported.

## Unsupported Artifacts

Do not publish:

- sdists, until source builds have an explicit Go toolchain story
- musllinux wheels, until the Go + musl shared-library loader issue is solved
- developer-machine wheels as official releases
- artifacts that require install-time native downloads
