# Betterleaks Python Integration Docs

This folder captures the project plan and technical decisions for building a
self-contained Python package for Betterleaks.

## Document Map

- [Project brief](project-brief.md): what this project is, why it exists, and
  what has already been verified.
- [Getting started](getting-started.md): install, local build, scan examples,
  Docker, and docs commands.
- [API reference](api.md): generated public Python API reference.
- [Workplan](workplan.md): phased implementation plan from scaffold to PyPI
  release.
- [Architecture](architecture.md): proposed package layout, native bridge
  design, public Python API, and CI/release model.
- [ABI contract](abi.md): JSON request/response shape and exported native
  functions.
- [Implementation notes](implementation-notes.md): detailed packaging,
  testing, compatibility, and supply-chain notes.
- [Betterleaks pin](betterleaks-pin.md): the bundled upstream version,
  provenance links, and upgrade checklist.
- [Release checklist](release-checklist.md): maintainer checklist for wheel and
  PyPI releases.
- [Troubleshooting](troubleshooting.md): common local build and install issues.
- [Roadmap](roadmap.md): follow-up features after the first working release.
- [v0.2 plan](v0.2-plan.md): config API, benchmarks, release hardening, and
  acceptance criteria for the next minor release.
- [AI handoff](ai-handoff.md): compact context for future AI agents and human
  maintainers.
- [Docker E2E](https://github.com/roymezan/pybetterleaks/tree/main/e2e):
  Docker end-to-end tests, fixtures, and runner.

## Current Status

Created on 2026-07-08. The repository now contains the initial Python SDK,
native ABI bridge, tests, Docker E2E harness, CI workflows, generated docs site,
and release docs.
