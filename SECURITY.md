# Security Policy

PyBetterleaks is a security-adjacent SDK, so reports should avoid posting real
secrets, private tokens, proprietary repositories, or exploitable details in
public issues.

## Supported Versions

Before `1.0.0`, security fixes target the latest published minor release. Older
alpha releases may be superseded quickly.

## Reporting A Vulnerability

Use GitHub private vulnerability reporting when it is enabled for the
repository. If that is not available, contact the maintainer privately before
opening a public issue.

Please include:

- the affected PyBetterleaks version
- platform and Python version
- whether the issue reproduces with upstream Betterleaks directly
- a minimal reproduction using synthetic secrets
- impact and any known workarounds

Do not include live credentials or customer data. Synthetic fixtures are enough.

## Scope

In scope:

- native bridge crashes or memory ownership bugs
- package-install behavior that downloads or executes unexpected code
- secret leakage through default redaction, errors, logs, or docs examples
- supply-chain problems in release artifacts

Out of scope:

- reports that require Alpine/musllinux wheels, which are currently unsupported
- upstream Betterleaks detection decisions that reproduce without PyBetterleaks
- benchmark-only performance differences without a security impact
