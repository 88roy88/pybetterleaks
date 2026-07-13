from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]

PYPROJECT = Path("pyproject.toml")
VERSION_MODULE = Path("python/pybetterleaks/_version.py")
UV_LOCK = Path("uv.lock")
AI_HANDOFF = Path("docs/ai-handoff.md")
IMPLEMENTATION_NOTES = Path("docs/implementation-notes.md")

STABLE_VERSION_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)$"
)
VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[a-zA-Z0-9.+-]+)?$")


@dataclass(frozen=True)
class VersionState:
    pyproject: str
    version_module: str
    uv_lock: str
    ai_handoff: Optional[str]
    implementation_notes: Optional[str]

    def values(self) -> list[str]:
        values = [self.pyproject, self.version_module, self.uv_lock]
        if self.ai_handoff is not None:
            values.append(self.ai_handoff)
        if self.implementation_notes is not None:
            values.append(self.implementation_notes)
        return values


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    state = read_version_state(root)

    if args.check:
        ensure_versions_match(state)
        print(f"Version sync OK: {state.pyproject}")
        return

    current = state.pyproject
    ensure_versions_match(state)
    new_version = args.version or bump_stable_version(current, args.part)
    validate_version(new_version)

    if args.dry_run:
        print(f"{current} -> {new_version}")
        return

    write_version(root, new_version)
    print(f"Bumped version: {current} -> {new_version}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bump or check PyBetterleaks version files.")
    parser.add_argument(
        "--root",
        default=ROOT,
        help="Repository root. Mainly useful for tests.",
    )
    parser.add_argument(
        "--part",
        choices=["patch", "minor", "major"],
        default="patch",
        help="Version component to bump when --version is omitted.",
    )
    parser.add_argument(
        "--version",
        default=None,
        help="Set an explicit version instead of bumping. Example: 0.6.0",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only verify that version-bearing files agree.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the version change without writing files.",
    )
    args = parser.parse_args()
    if args.check and (args.version is not None or args.part != "patch" or args.dry_run):
        raise SystemExit("--check cannot be combined with bump options")
    return args


def read_version_state(root: Path) -> VersionState:
    return VersionState(
        pyproject=read_pyproject_version(root / PYPROJECT),
        version_module=read_version_module(root / VERSION_MODULE),
        uv_lock=read_uv_lock_project_version(root / UV_LOCK),
        ai_handoff=read_optional_prefixed_version(
            root / AI_HANDOFF,
            "- Python package version in development: `",
        ),
        implementation_notes=read_optional_prefixed_version(
            root / IMPLEMENTATION_NOTES,
            "version = \"",
        ),
    )


def ensure_versions_match(state: VersionState) -> None:
    versions = state.values()
    expected = versions[0]
    mismatched = [version for version in versions if version != expected]
    if mismatched:
        raise SystemExit(f"version mismatch: {state}")


def read_pyproject_version(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, flags=re.MULTILINE)
    if match is None:
        raise RuntimeError(f"could not find project version in {path}")
    return match.group(1)


def read_version_module(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r'^__version__ = "([^"]+)"$', text, flags=re.MULTILINE)
    if match is None:
        raise RuntimeError(f"could not find __version__ in {path}")
    return match.group(1)


def read_uv_lock_project_version(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r'(\[\[package\]\]\nname = "pybetterleaks"\nversion = ")([^"]+)(")',
        text,
    )
    if match is None:
        raise RuntimeError(f"could not find pybetterleaks package in {path}")
    return match.group(2)


def read_optional_prefixed_version(path: Path, prefix: str) -> Optional[str]:
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            value = line.removeprefix(prefix)
            return value.split("`", 1)[0].split('"', 1)[0]
    return None


def validate_version(version: str) -> None:
    if VERSION_RE.fullmatch(version) is None:
        raise SystemExit(f"invalid version: {version!r}")


def bump_stable_version(version: str, part: str) -> str:
    match = STABLE_VERSION_RE.fullmatch(version)
    if match is None:
        raise SystemExit(f"cannot auto-bump non-stable version: {version}")

    major = int(match.group("major"))
    minor = int(match.group("minor"))
    patch = int(match.group("patch"))

    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def write_version(root: Path, version: str) -> None:
    replace_in_file(
        root / PYPROJECT,
        r'^(version = ")[^"]+(")$',
        rf"\g<1>{version}\2",
    )
    replace_in_file(
        root / VERSION_MODULE,
        r'^(__version__ = ")[^"]+(")$',
        rf"\g<1>{version}\2",
    )
    replace_in_file(
        root / UV_LOCK,
        r'(\[\[package\]\]\nname = "pybetterleaks"\nversion = ")[^"]+(")',
        rf"\g<1>{version}\2",
    )
    replace_in_file(
        root / AI_HANDOFF,
        r"^(- Python package version in development: `)[^`]+(`)$",
        rf"\g<1>{version}\2",
        required=False,
    )
    replace_in_file(
        root / IMPLEMENTATION_NOTES,
        r'^(version = ")[^"]+(")$',
        rf"\g<1>{version}\2",
        required=False,
    )


def replace_in_file(path: Path, pattern: str, replacement: str, *, required: bool = True) -> None:
    if not path.exists():
        if required:
            raise RuntimeError(f"file does not exist: {path}")
        return

    text = path.read_text(encoding="utf-8")
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        if required:
            raise RuntimeError(f"pattern not found in {path}: {pattern}")
        return
    path.write_text(new_text, encoding="utf-8")


if __name__ == "__main__":
    main()
