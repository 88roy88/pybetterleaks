from __future__ import annotations

from pathlib import Path

import pytest

from scripts import bump_version


def test_bump_version_updates_project_files(tmp_path: Path) -> None:
    write_version_fixture(tmp_path, "0.5.0")

    bump_version.write_version(tmp_path, "0.6.0")
    state = bump_version.read_version_state(tmp_path)

    assert state.pyproject == "0.6.0"
    assert state.version_module == "0.6.0"
    assert state.uv_lock == "0.6.0"
    assert state.ai_handoff == "0.6.0"
    assert state.implementation_notes == "0.6.0"


def test_bump_version_defaults_to_patch() -> None:
    assert bump_version.bump_stable_version("0.5.0", "patch") == "0.5.1"


def test_bump_version_can_bump_minor_and_major() -> None:
    assert bump_version.bump_stable_version("0.5.3", "minor") == "0.6.0"
    assert bump_version.bump_stable_version("0.5.3", "major") == "1.0.0"


def test_bump_version_rejects_auto_bump_for_non_stable_version() -> None:
    with pytest.raises(SystemExit):
        bump_version.bump_stable_version("0.6.0rc1", "patch")


def test_version_check_detects_mismatch(tmp_path: Path) -> None:
    write_version_fixture(tmp_path, "0.5.0")
    (tmp_path / "python/pybetterleaks/_version.py").write_text(
        '__version__ = "0.5.1"\n',
        encoding="utf-8",
    )

    with pytest.raises(SystemExit):
        bump_version.ensure_versions_match(bump_version.read_version_state(tmp_path))


def write_version_fixture(root: Path, version: str) -> None:
    (root / "python/pybetterleaks").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "pybetterleaks"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    (root / "python/pybetterleaks/_version.py").write_text(
        f'__version__ = "{version}"\n',
        encoding="utf-8",
    )
    (root / "uv.lock").write_text(
        f'[[package]]\nname = "pybetterleaks"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    (root / "docs/ai-handoff.md").write_text(
        f"- Python package version in development: `{version}`\n",
        encoding="utf-8",
    )
    (root / "docs/implementation-notes.md").write_text(
        f'version = "{version}"\n',
        encoding="utf-8",
    )
