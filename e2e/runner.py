from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from pybetterleaks import (
    BetterleaksConfig,
    Rule,
    ScanResult,
    betterleaks_version,
    scan_dir,
    scan_git,
    scan_text,
    scan_text_async,
)

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
CONFIG = FIXTURES / "betterleaks.toml"

ALPHA_SECRET = "PYBETTERLEAKS_ALPHA_0A1B2C3D4E5F6A7B"
BETA_SECRET = "PYBETTERLEAKS_BETA_8H7G6F5E4D3C2B1A"
INLINE_SECRET = "PYBETTERLEAKS_INLINE_0123456789ABCDEF"
GIT_SECRET = "PYBETTERLEAKS_GIT_0123456789ABCDEF"

EXPECTED_DIR_RULES = {
    "pybetterleaks-alpha",
    "pybetterleaks-beta",
    "pybetterleaks-gamma",
    "pybetterleaks-delta",
}


def main() -> None:
    assert_no_go_runtime()
    assert_version()
    assert_scan_text_redacted()
    assert_scan_text_unredacted()
    assert_scan_text_with_typed_config()
    assert_scan_text_async_with_typed_config()
    assert_scan_dir_finds_fixture_secrets()
    assert_scan_git_worktree_finds_only_worktree_files()
    assert_invalid_config_returns_structured_error()
    assert_scan_dir_rejects_file_targets()
    assert_timeout_input_validation()
    print("pybetterleaks docker e2e passed")


def assert_no_go_runtime() -> None:
    if os.environ.get("PYBETTERLEAKS_E2E_EXPECT_NO_GO") == "1":
        assert shutil.which("go") is None, "runtime image should not contain Go"


def assert_version() -> None:
    version = betterleaks_version()
    assert version.startswith("v"), version


def assert_scan_text_redacted() -> None:
    result = scan_text(ALPHA_SECRET, config_path=CONFIG, redact=True, validation=False)
    assert result.ok, result.errors
    assert _rule_ids(result) == {"pybetterleaks-alpha"}
    assert result.findings[0].secret == "REDACTED"


def assert_scan_text_unredacted() -> None:
    result = scan_text(BETA_SECRET, config_path=CONFIG, redact=False)
    assert result.ok, result.errors
    assert _rule_ids(result) == {"pybetterleaks-beta"}
    assert result.findings[0].secret == BETA_SECRET


def assert_scan_text_with_typed_config() -> None:
    result = scan_text(INLINE_SECRET, config=typed_config(), redact=False)
    assert result.ok, result.errors
    assert _rule_ids(result) == {"pybetterleaks-inline"}
    assert result.findings[0].secret == INLINE_SECRET


def assert_scan_text_async_with_typed_config() -> None:
    import asyncio

    result = asyncio.run(scan_text_async(INLINE_SECRET, config=typed_config(), redact=True))
    assert result.ok, result.errors
    assert _rule_ids(result) == {"pybetterleaks-inline"}
    assert result.findings[0].secret == "REDACTED"


def assert_scan_dir_finds_fixture_secrets() -> None:
    result = scan_dir(FIXTURES, config_path=CONFIG)
    assert result.ok, result.errors

    rule_ids = _rule_ids(result)
    missing = EXPECTED_DIR_RULES - rule_ids
    assert not missing, f"missing expected rules: {sorted(missing)}; got {sorted(rule_ids)}"

    files = {Path(finding.file or "").name for finding in result.findings}
    assert {"age.txt", "private-key.pem", "service.env", "worker.py"} <= files
    assert all(finding.secret == "REDACTED" for finding in result.findings)


def assert_scan_git_worktree_finds_only_worktree_files() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir) / "repo"
        source_dir = repo / "src"
        git_dir = repo / ".git"
        source_dir.mkdir(parents=True)
        git_dir.mkdir()
        (source_dir / "settings.env").write_text(
            f"PYBETTERLEAKS_GIT_TOKEN={GIT_SECRET}\n",
            encoding="utf-8",
        )
        (git_dir / "ignored.env").write_text(
            f"PYBETTERLEAKS_GIT_TOKEN={GIT_SECRET}\n",
            encoding="utf-8",
        )

        result = scan_git(repo, config=typed_git_config(), redact=False)

    assert result.ok, result.errors
    assert _rule_ids(result) == {"pybetterleaks-git"}
    assert len(result.findings) == 1
    assert result.findings[0].secret == GIT_SECRET
    assert result.findings[0].file is not None
    assert ".git" not in Path(result.findings[0].file).parts


def assert_invalid_config_returns_structured_error() -> None:
    result = scan_text(ALPHA_SECRET, config_path=FIXTURES / "missing-betterleaks.toml")
    assert not result.ok
    assert result.errors
    assert result.errors[0].code == "detector_init_failed"
    assert "missing-betterleaks.toml" in (result.errors[0].detail or "")


def assert_scan_dir_rejects_file_targets() -> None:
    result = scan_dir(FIXTURES / "secrets" / "age.txt")
    assert not result.ok
    assert result.errors
    assert result.errors[0].code == "target_not_directory"


def assert_timeout_input_validation() -> None:
    try:
        scan_text("nothing to scan", timeout_seconds=0)
    except ValueError as exc:
        assert "timeout_seconds" in str(exc)
    else:
        raise AssertionError("scan_text should reject non-positive timeout_seconds")


def typed_config() -> BetterleaksConfig:
    return BetterleaksConfig(
        rules=[
            Rule(
                id="pybetterleaks-inline",
                description="Synthetic inline PyBetterleaks fixture",
                regex=r"PYBETTERLEAKS_INLINE_[A-Z0-9]{16}",
                keywords=["PYBETTERLEAKS_INLINE_"],
            )
        ]
    )


def typed_git_config() -> BetterleaksConfig:
    return BetterleaksConfig(
        rules=[
            Rule(
                id="pybetterleaks-git",
                description="Synthetic Git PyBetterleaks fixture",
                regex=r"PYBETTERLEAKS_GIT_[A-Z0-9]{16}",
                keywords=["PYBETTERLEAKS_GIT_"],
            )
        ]
    )


def _rule_ids(result: ScanResult) -> set[str]:
    return {finding.rule_id for finding in result.findings}


if __name__ == "__main__":
    main()
