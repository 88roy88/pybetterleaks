"""Smoke test the package as installed from PyPI in a temporary venv."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

PACKAGE_NAME = "pybetterleaks"

SMOKE_CODE = r"""
from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

import pybetterleaks
from pybetterleaks import (
    BetterleaksConfig,
    Rule,
    betterleaks_version,
    scan_git,
    scan_text,
    scan_text_async,
)

expected_version = sys.argv[1]
secret = "PYBETTERLEAKS_PYPI_0123456789ABCDEF"
config = BetterleaksConfig(
    rules=[
        Rule(
            id="pybetterleaks-pypi-smoke",
            description="Synthetic PyPI smoke fixture",
            regex=r"PYBETTERLEAKS_PYPI_[A-Z0-9]{16}",
            keywords=["PYBETTERLEAKS_PYPI_"],
        )
    ]
)

assert pybetterleaks.__version__ == expected_version, pybetterleaks.__version__
assert betterleaks_version().startswith("v"), betterleaks_version()

text_result = scan_text(secret, config=config, redact=False)
assert text_result.ok, text_result.errors
assert {finding.rule_id for finding in text_result.findings} == {"pybetterleaks-pypi-smoke"}
assert text_result.findings[0].secret == secret

async_result = asyncio.run(scan_text_async(secret, config=config, redact=True))
assert async_result.ok, async_result.errors
assert async_result.findings[0].secret == "REDACTED"

with tempfile.TemporaryDirectory() as tmpdir:
    repo = Path(tmpdir) / "repo"
    git_dir = repo / ".git"
    git_dir.mkdir(parents=True)
    (repo / "settings.env").write_text(f"PYBETTERLEAKS_PYPI_TOKEN={secret}\n")
    (git_dir / "ignored.env").write_text(f"PYBETTERLEAKS_PYPI_TOKEN={secret}\n")

    git_result = scan_git(repo, config=config, redact=True)

assert git_result.ok, git_result.errors
assert len(git_result.findings) == 1, git_result.findings
assert git_result.findings[0].secret == "REDACTED"
assert git_result.findings[0].file is not None
assert ".git" not in Path(git_result.findings[0].file).parts

print(f"PyPI smoke passed for pybetterleaks {expected_version}")
"""


def main() -> None:
    args = parse_args()
    version = args.version or read_project_version()

    if args.retries < 1:
        raise SystemExit("--retries must be at least 1")

    with tempfile.TemporaryDirectory(prefix="pybetterleaks-pypi-smoke-") as tmpdir:
        temp_root = Path(tmpdir)
        venv = temp_root / "venv"
        run([args.python, "-m", "venv", str(venv)])

        venv_python_path = venv_python(venv)
        install_from_pypi(
            venv_python_path,
            package=args.package,
            version=version,
            retries=args.retries,
            retry_delay=args.retry_delay,
        )

        env = clean_python_env()
        run(
            [str(venv_python_path), "-c", SMOKE_CODE, version],
            cwd=temp_root,
            env=env,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", default=PACKAGE_NAME)
    parser.add_argument("--version", default=None)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--retries", type=int, default=6)
    parser.add_argument("--retry-delay", type=float, default=10.0)
    return parser.parse_args()


def read_project_version() -> str:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        if line.startswith("version = "):
            return line.split("=", 1)[1].strip().strip('"')
    raise RuntimeError(f"could not find project version in {pyproject}")


def venv_python(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def install_from_pypi(
    python: Path,
    *,
    package: str,
    version: str,
    retries: int,
    retry_delay: float,
) -> None:
    command = [
        str(python),
        "-m",
        "pip",
        "install",
        "--only-binary=:all:",
        f"{package}=={version}",
    ]
    env = clean_python_env()

    for attempt in range(1, retries + 1):
        try:
            run(command, env=env)
            return
        except subprocess.CalledProcessError:
            if attempt == retries:
                raise
            print(
                f"PyPI install attempt {attempt}/{retries} failed; "
                f"retrying in {retry_delay:g}s..."
            )
            time.sleep(retry_delay)


def clean_python_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    return env


def run(
    command: Sequence[str],
    *,
    cwd: Optional[Path] = None,
    env: Optional[dict[str, str]] = None,
) -> None:
    print("$", " ".join(display_command(command)), flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def display_command(command: Sequence[str]) -> list[str]:
    if len(command) >= 3 and command[1] == "-c":
        return [command[0], "-c", "<smoke code>", *command[3:]]
    return list(command)


if __name__ == "__main__":
    main()
