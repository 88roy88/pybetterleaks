"""Smoke test an installed PyBetterleaks wheel."""

from __future__ import annotations

import tempfile
from pathlib import Path

from pybetterleaks import betterleaks_version, scan_text

FAKE_WHEEL_SECRET = "PYBETTERLEAKS_WHEEL_0123456789ABCDEF"
FAKE_WHEEL_CONFIG = """
title = "PyBetterleaks wheel smoke"

[[rules]]
id = "pybetterleaks-wheel-smoke"
description = "Synthetic PyBetterleaks wheel smoke fixture"
regex = '''PYBETTERLEAKS_WHEEL_[A-Z0-9]{16}'''
keywords = ["PYBETTERLEAKS_WHEEL_"]
"""


def main() -> None:
    version = betterleaks_version()
    if not version.startswith("v"):
        raise AssertionError(f"unexpected Betterleaks version: {version!r}")

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "betterleaks.toml"
        config_path.write_text(FAKE_WHEEL_CONFIG, encoding="utf-8")
        result = scan_text(
            FAKE_WHEEL_SECRET,
            config_path=config_path,
            redact=True,
            validation=False,
        )

    if not result.ok:
        raise AssertionError(f"scan_text returned errors: {result.errors!r}")

    rule_ids = {finding.rule_id for finding in result.findings}
    if "pybetterleaks-wheel-smoke" not in rule_ids:
        raise AssertionError(
            f"expected pybetterleaks-wheel-smoke finding, got {sorted(rule_ids)!r}"
        )

    if not all(finding.secret == "REDACTED" for finding in result.findings):
        raise AssertionError("expected redacted findings by default")

    print(f"PyBetterleaks wheel smoke passed with Betterleaks {version}")


if __name__ == "__main__":
    main()
