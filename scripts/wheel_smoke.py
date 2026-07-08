"""Smoke test an installed PyBetterleaks wheel."""

from __future__ import annotations

import tempfile
from pathlib import Path

from pybetterleaks import (
    BetterleaksConfig,
    Rule,
    ScanResult,
    betterleaks_version,
    scan_text,
    scan_text_async,
)

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

    config = BetterleaksConfig(
        rules=[
            Rule(
                id="pybetterleaks-wheel-smoke-typed",
                description="Synthetic typed PyBetterleaks wheel smoke fixture",
                regex=r"PYBETTERLEAKS_WHEEL_[A-Z0-9]{16}",
                keywords=["PYBETTERLEAKS_WHEEL_"],
            )
        ]
    )
    result = scan_text(
        FAKE_WHEEL_SECRET,
        config=config,
        redact=True,
        validation=False,
    )
    assert_success(result, "pybetterleaks-wheel-smoke-typed")
    assert_async_success(config)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "betterleaks.toml"
        config_path.write_text(FAKE_WHEEL_CONFIG, encoding="utf-8")
        result = scan_text(
            FAKE_WHEEL_SECRET,
            config_path=config_path,
            redact=True,
            validation=False,
        )

    assert_success(result, "pybetterleaks-wheel-smoke")
    print(f"PyBetterleaks wheel smoke passed with Betterleaks {version}")


def assert_async_success(config: BetterleaksConfig) -> None:
    import asyncio

    result = asyncio.run(
        scan_text_async(
            FAKE_WHEEL_SECRET,
            config=config,
            redact=True,
            validation=False,
        )
    )
    assert_success(result, "pybetterleaks-wheel-smoke-typed")


def assert_success(result: ScanResult, rule_id: str) -> None:
    if not result.ok:
        raise AssertionError(f"scan_text returned errors: {result.errors!r}")

    rule_ids = {finding.rule_id for finding in result.findings}
    if rule_id not in rule_ids:
        raise AssertionError(f"expected {rule_id} finding, got {sorted(rule_ids)!r}")

    if not all(finding.secret == "REDACTED" for finding in result.findings):
        raise AssertionError("expected redacted findings by default")


if __name__ == "__main__":
    main()
