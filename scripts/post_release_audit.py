from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, TypeVar, cast

PACKAGE_NAME = "pybetterleaks"
REPO = "roymezan/pybetterleaks"
T = TypeVar("T")


@dataclass(frozen=True)
class ReleaseFile:
    filename: str
    sha256: str
    packagetype: str


@dataclass(frozen=True)
class GitHubAsset:
    name: str
    download_url: str


def main() -> None:
    args = parse_args()

    pypi_data = retry(
        lambda: fetch_json(f"https://pypi.org/pypi/{args.package}/json"),
        retries=args.retries,
        delay=args.retry_delay,
        label="PyPI metadata",
    )
    release_files = retry(
        lambda: validate_pypi_release(pypi_data, version=args.version),
        retries=args.retries,
        delay=args.retry_delay,
        label=f"PyPI release {args.version}",
    )

    if not args.skip_github:
        github_release = retry(
            lambda: fetch_json(
                f"https://api.github.com/repos/{args.repo}/releases/tags/v{args.version}"
            ),
            retries=args.retries,
            delay=args.retry_delay,
            label=f"GitHub release v{args.version}",
        )
        checksum_asset = find_asset(github_release, "SHA256SUMS")
        checksum_text = fetch_text(checksum_asset.download_url)
        checksum_entries = parse_checksums(checksum_text)
        validate_checksums(release_files, checksum_entries)

    if not args.skip_install_smoke:
        run_pypi_smoke(args.version, package=args.package)

    print(f"Post-release audit passed for {args.package} {args.version}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit a published PyBetterleaks release.")
    parser.add_argument("--version", required=True, help="Version to audit, without leading v.")
    parser.add_argument("--package", default=PACKAGE_NAME)
    parser.add_argument("--repo", default=REPO, help="GitHub repo in owner/name form.")
    parser.add_argument("--retries", type=int, default=6)
    parser.add_argument("--retry-delay", type=float, default=10.0)
    parser.add_argument("--skip-github", action="store_true")
    parser.add_argument("--skip-install-smoke", action="store_true")
    args = parser.parse_args()
    if args.retries < 1:
        raise SystemExit("--retries must be at least 1")
    if args.retry_delay < 0:
        raise SystemExit("--retry-delay cannot be negative")
    return args


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return cast(dict[str, Any], json.load(response))


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"Accept": "text/plain"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return cast(str, response.read().decode("utf-8"))


def retry(
    func: Callable[[], T],
    *,
    retries: int,
    delay: float,
    label: str,
) -> T:
    last_error: Optional[BaseException] = None
    for attempt in range(1, retries + 1):
        try:
            return func()
        except Exception as error:
            last_error = error
            if attempt == retries:
                break
            print(f"{label} attempt {attempt}/{retries} failed; retrying in {delay:g}s...")
            time.sleep(delay)
    raise SystemExit(f"{label} failed after {retries} attempt(s): {last_error}")


def validate_pypi_release(data: dict[str, Any], *, version: str) -> list[ReleaseFile]:
    releases = data.get("releases")
    if not isinstance(releases, dict):
        raise ValueError("PyPI JSON is missing releases")

    files = releases.get(version)
    if not files:
        raise ValueError(f"PyPI release {version} is not visible yet")

    release_files: list[ReleaseFile] = []
    for file_data in files:
        filename = file_data.get("filename")
        packagetype = file_data.get("packagetype")
        digests = file_data.get("digests") or {}
        sha256 = digests.get("sha256")
        if not isinstance(filename, str) or not isinstance(packagetype, str):
            raise ValueError(f"invalid PyPI file metadata: {file_data!r}")
        if not isinstance(sha256, str):
            raise ValueError(f"missing sha256 digest for {filename}")
        if "musllinux" in filename:
            raise ValueError(f"musllinux artifact must not be published: {filename}")
        release_files.append(ReleaseFile(filename=filename, sha256=sha256, packagetype=packagetype))

    wheel_files = [
        release_file for release_file in release_files if release_file.filename.endswith(".whl")
    ]
    if not wheel_files:
        raise ValueError(f"PyPI release {version} has no wheels")
    return release_files


def find_asset(release_data: dict[str, Any], name: str) -> GitHubAsset:
    assets = release_data.get("assets")
    if not isinstance(assets, list):
        raise ValueError("GitHub release JSON is missing assets")
    for asset in assets:
        asset_name = asset.get("name")
        download_url = asset.get("browser_download_url")
        if asset_name == name and isinstance(download_url, str):
            return GitHubAsset(name=asset_name, download_url=download_url)
    raise ValueError(f"GitHub release is missing {name}")


def parse_checksums(text: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"SHA256SUMS:{line_number}: invalid checksum line")
        digest, filename = parts
        filename = filename.strip()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError(f"SHA256SUMS:{line_number}: invalid sha256 digest")
        if Path(filename).name != filename:
            raise ValueError(f"SHA256SUMS:{line_number}: checksum filename must not contain paths")
        entries[filename] = digest
    if not entries:
        raise ValueError("SHA256SUMS is empty")
    return entries


def validate_checksums(
    release_files: list[ReleaseFile],
    checksum_entries: dict[str, str],
) -> None:
    expected = {release_file.filename: release_file.sha256 for release_file in release_files}
    missing = expected.keys() - checksum_entries.keys()
    extra = checksum_entries.keys() - expected.keys()
    if missing:
        raise ValueError(f"SHA256SUMS is missing PyPI file(s): {sorted(missing)!r}")
    if extra:
        raise ValueError(f"SHA256SUMS contains non-PyPI file(s): {sorted(extra)!r}")
    mismatched = [
        filename
        for filename, expected_hash in expected.items()
        if checksum_entries[filename] != expected_hash
    ]
    if mismatched:
        raise ValueError(f"SHA256SUMS digest mismatch for: {mismatched!r}")


def run_pypi_smoke(version: str, *, package: str) -> None:
    script = Path(__file__).with_name("pypi_smoke.py")
    subprocess.run(
        [
            sys.executable,
            str(script),
            "--package",
            package,
            "--version",
            version,
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
