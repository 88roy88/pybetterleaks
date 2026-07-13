from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pybetterleaks import (
    BetterleaksConfig,
    Rule,
    ScanResult,
    betterleaks_version,
    scan_dir,
    scan_text,
)

SECRET = "PYBETTERLEAKS_BENCH_0123456789ABCDEF"
SUBPROCESS_SCAN_CODE = r"""
from __future__ import annotations

import sys
from pathlib import Path

from pybetterleaks import scan_dir, scan_text

mode = sys.argv[1]
target = sys.argv[2]
config_path = Path(sys.argv[3])

if mode == "text":
    result = scan_text(target, config_path=config_path, redact=True, raise_on_error=True)
elif mode == "dir":
    result = scan_dir(target, config_path=config_path, redact=True, raise_on_error=True)
else:
    raise SystemExit(f"unsupported benchmark mode: {mode}")

if not result.findings:
    raise SystemExit("benchmark scan produced no findings")
"""


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    fixture: str
    run: Callable[[], object]


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    fixture: str
    samples_ms: list[float]

    @property
    def mean_ms(self) -> float:
        return statistics.mean(self.samples_ms)

    @property
    def median_ms(self) -> float:
        return statistics.median(self.samples_ms)

    @property
    def min_ms(self) -> float:
        return min(self.samples_ms)

    @property
    def max_ms(self) -> float:
        return max(self.samples_ms)

    def to_json(self) -> dict[str, object]:
        return {
            "name": self.name,
            "fixture": self.fixture,
            "samples_ms": [round(sample, 4) for sample in self.samples_ms],
            "mean_ms": round(self.mean_ms, 4),
            "median_ms": round(self.median_ms, 4),
            "min_ms": round(self.min_ms, 4),
            "max_ms": round(self.max_ms, 4),
        }


def main() -> None:
    args = parse_args()
    report = run_benchmarks(args)
    print(format_console_report(report))

    if args.json_output is not None:
        write_json_report(Path(args.json_output), report)
    if args.markdown_output is not None:
        Path(args.markdown_output).write_text(format_markdown_report(report), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run synthetic PyBetterleaks benchmarks.")
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--files", type=int, default=50)
    parser.add_argument("--secrets-per-file", type=int, default=2)
    parser.add_argument("--cli", action="store_true", help="Include Betterleaks CLI baseline.")
    parser.add_argument("--cli-path", default=None, help="Path to Betterleaks CLI executable.")
    parser.add_argument(
        "--subprocess-wrapper",
        action="store_true",
        help="Include Python subprocess wrapper baselines.",
    )
    parser.add_argument("--json-output", default=None, help="Write benchmark report JSON.")
    parser.add_argument("--markdown-output", default=None, help="Write benchmark report Markdown.")
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


def run_benchmarks(args: argparse.Namespace) -> dict[str, object]:
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

        cases = benchmark_cases(
            args,
            config=config,
            fixture_dir=fixture_dir,
            config_path=config_path,
        )
        results = [run_case(case, warmups=args.warmups, rounds=args.rounds) for case in cases]

    return {
        "schema_version": 1,
        "package": "pybetterleaks",
        "betterleaks_version": betterleaks_version(),
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "executable": sys.executable,
        "fixture": {
            "files": args.files,
            "secrets_per_file": args.secrets_per_file,
        },
        "warmups": args.warmups,
        "rounds": args.rounds,
        "cases": [result.to_json() for result in results],
    }


def benchmark_cases(
    args: argparse.Namespace,
    *,
    config: BetterleaksConfig,
    fixture_dir: Path,
    config_path: Path,
) -> list[BenchmarkCase]:
    text_fixture = "one synthetic secret"
    dir_fixture = f"{args.files} files, {args.secrets_per_file} secrets per file"

    cases = [
        BenchmarkCase(
            "pybetterleaks.scan_text",
            text_fixture,
            lambda: assert_scan_result(scan_text(SECRET, config=config, redact=True)),
        ),
        BenchmarkCase(
            "pybetterleaks.scan_dir",
            dir_fixture,
            lambda: assert_scan_result(scan_dir(fixture_dir, config=config, redact=True)),
        ),
    ]

    if args.subprocess_wrapper:
        cases.extend(
            [
                BenchmarkCase(
                    "python subprocess scan_text",
                    text_fixture,
                    lambda: run_subprocess_wrapper("text", SECRET, config_path),
                ),
                BenchmarkCase(
                    "python subprocess scan_dir",
                    dir_fixture,
                    lambda: run_subprocess_wrapper("dir", str(fixture_dir), config_path),
                ),
            ]
        )

    if args.cli:
        cli = args.cli_path or shutil.which("betterleaks")
        if cli is None:
            raise SystemExit("Betterleaks CLI not found; pass --cli-path or update PATH")
        cases.append(
            BenchmarkCase(
                "betterleaks cli dir",
                dir_fixture,
                lambda: run_cli(cli, fixture_dir, config_path),
            )
        )

    return cases


def write_fixtures(root: Path, *, files: int, secrets_per_file: int) -> None:
    root.mkdir(parents=True)
    for index in range(files):
        lines = [f"# synthetic file {index}"]
        for secret_index in range(secrets_per_file):
            lines.append(f"token_{secret_index} = {SECRET}")
        lines.append("safe_value = PYBETTERLEAKS_NOT_A_SECRET")
        (root / f"fixture_{index:04d}.txt").write_text("\n".join(lines), encoding="utf-8")


def assert_scan_result(result: ScanResult) -> None:
    if not result.ok:
        raise AssertionError(f"benchmark scan returned errors: {result.errors!r}")
    if not result.findings:
        raise AssertionError("benchmark scan produced no findings")


def run_subprocess_wrapper(mode: str, target: str, config_path: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            "-c",
            SUBPROCESS_SCAN_CODE,
            mode,
            target,
            str(config_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=clean_python_env(),
    )


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


def run_case(case: BenchmarkCase, *, warmups: int, rounds: int) -> BenchmarkResult:
    for _ in range(warmups):
        case.run()
    samples = [measure_ms(case.run) for _ in range(rounds)]
    return BenchmarkResult(name=case.name, fixture=case.fixture, samples_ms=samples)


def measure_ms(func: Callable[[], object]) -> float:
    start = time.perf_counter()
    func()
    return (time.perf_counter() - start) * 1000


def format_console_report(report: dict[str, object]) -> str:
    fixture = require_dict(report["fixture"])
    lines = [
        f"files={fixture['files']} secrets_per_file={fixture['secrets_per_file']}",
        f"warmups={report['warmups']} rounds={report['rounds']}",
    ]
    for case in require_list(report["cases"]):
        case_report = require_dict(case)
        lines.append(format_result(case_report))
    return "\n".join(lines)


def format_result(case: dict[str, object]) -> str:
    return (
        f"{case['name']}: mean={case['mean_ms']:.2f}ms "
        f"median={case['median_ms']:.2f}ms min={case['min_ms']:.2f}ms "
        f"max={case['max_ms']:.2f}ms"
    )


def format_markdown_report(report: dict[str, object]) -> str:
    lines = [
        "# PyBetterleaks Benchmark Results",
        "",
        f"- Betterleaks: `{report['betterleaks_version']}`",
        f"- Python: `{report['python_implementation']} {report['python']}`",
        f"- Platform: `{report['platform']}`",
        f"- Warmups: `{report['warmups']}`",
        f"- Rounds: `{report['rounds']}`",
        "",
        "| Case | Fixture | Mean | Median | Min | Max |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for case in require_list(report["cases"]):
        case_report = require_dict(case)
        lines.append(
            "| {name} | {fixture} | {mean_ms:.2f} ms | {median_ms:.2f} ms | "
            "{min_ms:.2f} ms | {max_ms:.2f} ms |".format(**case_report)
        )
    return "\n".join(lines) + "\n"


def write_json_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def clean_python_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    return env


def require_dict(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"expected dict, got {type(value).__name__}")
    return value


def require_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"expected list, got {type(value).__name__}")
    return value


if __name__ == "__main__":
    main()
