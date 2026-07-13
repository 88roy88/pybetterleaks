# Betterleaks Python Integration Docs

This folder captures both the public documentation and the repo-only planning
record for PyBetterleaks.

## Public Website Pages

These pages are included in the MkDocs site:

- [Home](index.md): product overview and quick links.
- [Getting started](getting-started.md): install, local build, scan examples,
  Docker, and docs commands.
- [Configuration](configuration.md): typed config models, Betterleaks TOML
  mapping, Expr filters, validation helpers, common rule helpers, relative
  extend paths, and validation env vars.
- [Git scanning](git-scanning.md): local worktree scanning, supported scope,
  async Git scans, and deferred Git source modes.
- [API reference](api.md): generated public Python API reference.
- [Benchmarks](benchmarks.md): current synthetic benchmark results,
  reproduction commands, and interpretation notes.
- [Troubleshooting](troubleshooting.md): common local build and install issues.
- [Betterleaks pin](betterleaks-pin.md): bundled upstream version, provenance
  links, and upgrade checklist.
- [Supply chain](supply-chain.md): trusted publishing, artifact inspection,
  checksums, provenance, and deferred SBOM work.
- [Deprecation policy](deprecation-policy.md): compatibility promises and
  breaking-change rules before and after `1.0.0`.

## Repo-Only Docs

These files stay in the repository for future AI agents and human maintainers,
but are excluded from the public MkDocs build with `exclude_docs`:

- [Project brief](project-brief.md): original project context and verified
  assumptions.
- [Workplan](workplan.md): phased implementation plan from scaffold to PyPI
  release.
- [Architecture](architecture.md): package layout, native bridge design, public
  Python API, and CI/release model.
- [ABI contract](abi.md): JSON request/response shape and exported native
  functions.
- [Implementation notes](implementation-notes.md): detailed packaging,
  testing, compatibility, and supply-chain notes.
- [Release checklist](release-checklist.md): maintainer checklist for wheel and
  PyPI releases.
- [v1.0 readiness](v1-readiness.md): release-readiness criteria and suggested
  path to a stable `1.0.0`.
- [Roadmap](roadmap.md): release scope, blocked musllinux work, and follow-up
  features.
- [Backlog](backlog.md): unsupported features, future tasks, and open
  decisions.
- [v0.2 plan](v0.2-plan.md): config API, async cancellation, benchmarks,
  release hardening, and acceptance criteria.
- [v0.3 plan](v0.3-plan.md): Git workflows, deferred streaming/API decisions,
  config coverage, and release hardening.
- [v0.4 plan](v0.4-plan.md): completed config-helper sweep, async cancellation
  hardening, release metadata, and acceptance criteria.
- [v0.5 plan](v0.5-plan.md): release hardening, artifact inspection,
  provenance, checksums, and deprecation policy.
- [v0.6 plan](v0.6-plan.md): release branch workflow, version automation,
  post-release audit, benchmark artifacts, and project polish.
- [AI handoff](ai-handoff.md): compact context for future AI agents and human
  maintainers.
- [Docs map](docs-map.md): this repo-only index.

## Current Status

Created on 2026-07-08 and updated after the first PyPI release on 2026-07-09.
The repository now contains the Python SDK, native ABI bridge, typed config API,
async wrappers, tests, Docker E2E harness, CI workflows, generated docs site,
benchmarks, and release docs.
