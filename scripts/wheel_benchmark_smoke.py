"""Run a tiny benchmark from a clean wheel install in a temporary venv."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    args = parse_args()
    wheel = find_wheel(Path(args.wheel))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="pybetterleaks-wheel-bench-") as tmpdir:
        temp_root = Path(tmpdir)
        venv = temp_root / "venv"
        run([sys.executable, "-m", "venv", str(venv)])
        python = venv_python(venv)
        run(
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
            env=clean_python_env(),
        )
        run(
            [
                str(python),
                str(ROOT / "benchmarks" / "bench.py"),
                "--rounds",
                str(args.rounds),
                "--warmups",
                str(args.warmups),
                "--files",
                str(args.files),
                "--secrets-per-file",
                str(args.secrets_per_file),
                "--subprocess-wrapper",
                "--json-output",
                str(output_dir / "wheel-benchmark.json"),
                "--markdown-output",
                str(output_dir / "wheel-benchmark.md"),
            ],
            cwd=temp_root,
            env=clean_python_env(),
        )

    print(f"Wheel benchmark smoke wrote {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--wheel",
        default="wheelhouse",
        help="Wheel file or directory containing exactly one wheel.",
    )
    parser.add_argument("--output-dir", default="benchmark-results")
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--warmups", type=int, default=0)
    parser.add_argument("--files", type=int, default=5)
    parser.add_argument("--secrets-per-file", type=int, default=1)
    return parser.parse_args()


def find_wheel(path: Path) -> Path:
    if path.is_file():
        if path.suffix != ".whl":
            raise SystemExit(f"not a wheel file: {path}")
        return path.resolve()

    if not path.is_dir():
        raise SystemExit(f"wheel path does not exist: {path}")

    wheels = sorted(path.glob("*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"expected exactly one wheel in {path}, found {len(wheels)}")
    return wheels[0].resolve()


def venv_python(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


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
    print("$", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


if __name__ == "__main__":
    main()
