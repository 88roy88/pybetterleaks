"""Smoke test an installed PyBetterleaks wheel."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

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
    if len(sys.argv) > 1 and not os.environ.get("PYBETTERLEAKS_WHEEL_SMOKE_INSTALLED"):
        run_from_wheel(Path(sys.argv[1]))
        return

    run_smoke()


def run_from_wheel(wheel_path: Path) -> None:
    wheel = wheel_path.resolve()
    if not wheel.exists():
        raise AssertionError(f"wheel does not exist: {wheel}")

    with tempfile.TemporaryDirectory() as tmpdir:
        venv = Path(tmpdir) / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        python = venv_python(venv)
        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                "--force-reinstall",
                str(wheel),
            ],
            check=True,
        )
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env["PYBETTERLEAKS_WHEEL_SMOKE_INSTALLED"] = "1"
        subprocess.run(
            [str(python), str(Path(__file__).resolve())],
            check=True,
            cwd=tmpdir,
            env=env,
        )


def venv_python(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def run_smoke() -> None:
    from pybetterleaks import (
        BetterleaksConfig,
        Expr,
        Rule,
        Validation,
        betterleaks_version,
        scan_git,
        scan_text,
    )

    version = betterleaks_version()
    if not version.startswith("v"):
        raise AssertionError(f"unexpected Betterleaks version: {version!r}")

    config = BetterleaksConfig(
        rules=[
            Rule.prefixed_token_rule(
                id="pybetterleaks-wheel-smoke-typed",
                description="Synthetic typed PyBetterleaks wheel smoke fixture",
                prefix="PYBETTERLEAKS_WHEEL_",
                token_pattern=r"[A-Z0-9]{16}",
                filter=Expr.finding_contains_any(["SKIP_ME"]),
                validate=Validation.needs_validation(),
            )
        ]
    )
    result = scan_text(
        FAKE_WHEEL_SECRET,
        config=config,
        redact=True,
        validation=True,
    )
    assert_success(result, "pybetterleaks-wheel-smoke-typed")
    assert_validation_status(result, "pybetterleaks-wheel-smoke-typed", "needs_validation")
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
        repo = Path(tmpdir) / "repo"
        git_dir = repo / ".git"
        git_dir.mkdir(parents=True)
        (repo / "wheel.env").write_text(
            f"PYBETTERLEAKS_WHEEL_TOKEN={FAKE_WHEEL_SECRET}\n",
            encoding="utf-8",
        )
        (git_dir / "ignored.env").write_text(
            f"PYBETTERLEAKS_WHEEL_TOKEN={FAKE_WHEEL_SECRET}\n",
            encoding="utf-8",
        )
        git_result = scan_git(
            repo,
            config=config,
            redact=True,
            validation=False,
        )

    assert_success(result, "pybetterleaks-wheel-smoke")
    assert_success(git_result, "pybetterleaks-wheel-smoke-typed")
    if len(git_result.findings) != 1:
        raise AssertionError(f"expected one worktree finding, got {git_result.findings!r}")
    print(f"PyBetterleaks wheel smoke passed with Betterleaks {version}")


def assert_async_success(config) -> None:
    import asyncio

    from pybetterleaks import scan_text_async

    result = asyncio.run(
        scan_text_async(
            FAKE_WHEEL_SECRET,
            config=config,
            redact=True,
            validation=False,
        )
    )
    assert_success(result, "pybetterleaks-wheel-smoke-typed")


def assert_success(result, rule_id: str) -> None:
    if not result.ok:
        raise AssertionError(f"scan returned errors: {result.errors!r}")

    rule_ids = {finding.rule_id for finding in result.findings}
    if rule_id not in rule_ids:
        raise AssertionError(f"expected {rule_id} finding, got {sorted(rule_ids)!r}")

    if not all(finding.secret == "REDACTED" for finding in result.findings):
        raise AssertionError("expected redacted findings by default")


def assert_validation_status(result, rule_id: str, status: str) -> None:
    if not any(
        finding.rule_id == rule_id and finding.validation_status == status
        for finding in result.findings
    ):
        raise AssertionError(f"expected {rule_id} validation status {status!r}")


if __name__ == "__main__":
    main()
