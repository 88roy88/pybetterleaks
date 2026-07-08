from __future__ import annotations

import argparse
import shutil
import statistics
import subprocess
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from pybetterleaks import BetterleaksConfig, Rule, scan_dir, scan_text

SECRET = "PYBETTERLEAKS_BENCH_0123456789ABCDEF"


def main() -> None:
    args = parse_args()
    config = BetterleaksConfig(
        rules=[
            Rule(
                id="pybetterleaks-bench",
                description="Synthetic PyBetterleaks benchmark rule",
                regex=r"PYBETTERLEAKS_BENCH_[A-Z0-9]{16}",
                keywords=["PYBETTERLEAKS_BENCH_"],
            )
        ]
    )

    with tempfile.TemporaryDirectory(prefix="pybetterleaks-bench-") as tmpdir:
        root = Path(tmpdir)
        fixture_dir = root / "fixtures"
        config_path = config.write(root / "betterleaks.toml")
        write_fixtures(fixture_dir, files=args.files, secrets_per_file=args.secrets_per_file)

        cases: list[tuple[str, Callable[[], object]]] = [
            (
                "pybetterleaks.scan_text",
                lambda: scan_text(SECRET, config=config, redact=True),
            ),
            (
                "pybetterleaks.scan_dir",
                lambda: scan_dir(fixture_dir, config=config, redact=True),
            ),
        ]

        if args.cli:
            cli = args.cli_path or shutil.which("betterleaks")
            if cli is None:
                raise SystemExit("Betterleaks CLI not found; pass --cli-path or update PATH")
            cases.append(
                (
                    "betterleaks cli dir",
                    lambda: run_cli(cli, fixture_dir, config_path),
                )
            )

        print(f"files={args.files} secrets_per_file={args.secrets_per_file}")
        print(f"warmups={args.warmups} rounds={args.rounds}")
        for name, func in cases:
            for _ in range(args.warmups):
                func()
            samples = [measure(func) for _ in range(args.rounds)]
            print(format_result(name, samples))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run synthetic PyBetterleaks benchmarks.")
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--files", type=int, default=50)
    parser.add_argument("--secrets-per-file", type=int, default=2)
    parser.add_argument("--cli", action="store_true", help="Include Betterleaks CLI baseline.")
    parser.add_argument("--cli-path", default=None, help="Path to Betterleaks CLI executable.")
    args = parser.parse_args()
    if args.rounds <= 0:
        raise SystemExit("--rounds must be greater than zero")
    if args.warmups < 0:
        raise SystemExit("--warmups cannot be negative")
    if args.files <= 0:
        raise SystemExit("--files must be greater than zero")
    if args.secrets_per_file <= 0:
        raise SystemExit("--secrets-per-file must be greater than zero")
    return args


def write_fixtures(root: Path, *, files: int, secrets_per_file: int) -> None:
    root.mkdir(parents=True)
    for index in range(files):
        lines = [f"# synthetic file {index}"]
        for secret_index in range(secrets_per_file):
            lines.append(f"token_{secret_index} = {SECRET}")
        lines.append("safe_value = PYBETTERLEAKS_NOT_A_SECRET")
        (root / f"fixture_{index:04d}.txt").write_text("\n".join(lines), encoding="utf-8")


def run_cli(cli: str, fixture_dir: Path, config_path: Path) -> None:
    subprocess.run(
        [
            cli,
            "dir",
            "--config",
            str(config_path),
            "--redact",
            "100",
            "--exit-code",
            "0",
            str(fixture_dir),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def measure(func: Callable[[], object]) -> float:
    start = time.perf_counter()
    func()
    return time.perf_counter() - start


def format_result(name: str, samples: list[float]) -> str:
    mean_ms = statistics.mean(samples) * 1000
    median_ms = statistics.median(samples) * 1000
    minimum_ms = min(samples) * 1000
    maximum_ms = max(samples) * 1000
    return (
        f"{name}: mean={mean_ms:.2f}ms median={median_ms:.2f}ms "
        f"min={minimum_ms:.2f}ms max={maximum_ms:.2f}ms"
    )


if __name__ == "__main__":
    main()
