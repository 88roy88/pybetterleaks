from pathlib import Path

import pytest
from pybetterleaks import BetterleaksConfig, Rule, _native
from pybetterleaks.scanner import scan_dir, scan_git, scan_text

FIXTURES = Path(__file__).resolve().parents[1] / "e2e" / "fixtures"
FIXTURE_CONFIG = FIXTURES / "betterleaks.toml"
FAKE_ALPHA_SECRET = "PYBETTERLEAKS_ALPHA_0A1B2C3D4E5F6A7B"


@pytest.mark.native
def test_native_version_when_library_is_available() -> None:
    if not _native.native_library_path().exists():
        pytest.skip("native library has not been built")

    assert _native.betterleaks_version().startswith("v")


@pytest.mark.native
def test_native_scan_text_when_library_is_available() -> None:
    if not _native.native_library_path().exists():
        pytest.skip("native library has not been built")

    result = scan_text(FAKE_ALPHA_SECRET, config_path=FIXTURE_CONFIG)

    assert result.betterleaks_version.startswith("v")
    assert result.ok
    assert len(result.findings) == 1
    assert result.findings[0].rule_id == "pybetterleaks-alpha"
    assert result.findings[0].secret == "REDACTED"


@pytest.mark.native
def test_native_scan_text_with_typed_config_when_library_is_available() -> None:
    if not _native.native_library_path().exists():
        pytest.skip("native library has not been built")

    config = BetterleaksConfig(
        rules=[
            Rule(
                id="pybetterleaks-typed",
                description="Synthetic typed config fixture",
                regex=r"PYBETTERLEAKS_TYPED_[A-Z0-9]{16}",
                keywords=["PYBETTERLEAKS_TYPED_"],
            )
        ]
    )

    result = scan_text("PYBETTERLEAKS_TYPED_0123456789ABCDEF", config=config, redact=False)

    assert result.ok, result.errors
    assert len(result.findings) == 1
    assert result.findings[0].rule_id == "pybetterleaks-typed"
    assert result.findings[0].secret == "PYBETTERLEAKS_TYPED_0123456789ABCDEF"


@pytest.mark.native
def test_native_validation_env_vars_when_library_is_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not _native.native_library_path().exists():
        pytest.skip("native library has not been built")

    monkeypatch.setenv("PYBETTERLEAKS_VALIDATION_RESULT", "valid")
    config = BetterleaksConfig(
        rules=[
            Rule(
                id="pybetterleaks-validation-env",
                description="Synthetic validation env fixture",
                regex=r"PYBETTERLEAKS_VALIDATION_[A-Z0-9]{16}",
                keywords=["PYBETTERLEAKS_VALIDATION_"],
                validate=(
                    'env.get("PYBETTERLEAKS_VALIDATION_RESULT") == "valid" ? '
                    '{"result": "valid"} : {"result": "invalid"}'
                ),
            )
        ]
    )

    result = scan_text(
        "PYBETTERLEAKS_VALIDATION_0123456789ABCDEF",
        config=config,
        validation=True,
        validation_env_vars=["PYBETTERLEAKS_VALIDATION_RESULT"],
        redact=False,
    )

    assert result.ok, result.errors
    assert len(result.findings) == 1
    assert result.findings[0].validation_status == "valid"


@pytest.mark.native
def test_native_scan_dir_when_library_is_available() -> None:
    if not _native.native_library_path().exists():
        pytest.skip("native library has not been built")

    result = scan_dir(FIXTURES, config_path=FIXTURE_CONFIG)

    assert result.ok
    rule_ids = {finding.rule_id for finding in result.findings}
    assert {
        "pybetterleaks-alpha",
        "pybetterleaks-beta",
        "pybetterleaks-gamma",
        "pybetterleaks-delta",
    } <= rule_ids
    assert all(finding.file for finding in result.findings)
    assert all(finding.secret == "REDACTED" for finding in result.findings)


@pytest.mark.native
def test_native_scan_git_worktree_when_library_is_available(tmp_path: Path) -> None:
    if not _native.native_library_path().exists():
        pytest.skip("native library has not been built")

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "app.env").write_text(
        "PYBETTERLEAKS_GIT_0123456789ABCDEF\n",
        encoding="utf-8",
    )
    (repo / ".git" / "ignored.env").write_text(
        "PYBETTERLEAKS_GIT_IGNORED_0123456789ABCDEF\n",
        encoding="utf-8",
    )
    config = BetterleaksConfig(
        rules=[
            Rule(
                id="pybetterleaks-git",
                description="Synthetic git worktree fixture",
                regex=r"PYBETTERLEAKS_GIT_[A-Z0-9]{16}",
                keywords=["PYBETTERLEAKS_GIT_"],
            )
        ]
    )

    result = scan_git(repo, config=config, redact=False)

    assert result.ok, result.errors
    assert len(result.findings) == 1
    assert result.findings[0].rule_id == "pybetterleaks-git"
    assert result.findings[0].secret == "PYBETTERLEAKS_GIT_0123456789ABCDEF"


@pytest.mark.native
def test_native_scan_git_non_repo_returns_structured_error_when_library_is_available(
    tmp_path: Path,
) -> None:
    if not _native.native_library_path().exists():
        pytest.skip("native library has not been built")

    result = scan_git(tmp_path)

    assert not result.ok
    assert result.errors
    assert result.errors[0].code == "target_not_git_repository"


@pytest.mark.native
def test_native_invalid_config_returns_structured_error_when_library_is_available() -> None:
    if not _native.native_library_path().exists():
        pytest.skip("native library has not been built")

    result = scan_text(FAKE_ALPHA_SECRET, config_path=FIXTURES / "missing-betterleaks.toml")

    assert not result.ok
    assert result.errors
    assert result.errors[0].code == "detector_init_failed"
