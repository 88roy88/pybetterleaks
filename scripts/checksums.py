from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def main() -> None:
    args = parse_args()
    root = Path(args.directory)
    if not root.exists():
        raise SystemExit(f"directory does not exist: {root}")

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path

    output_resolved = output_path.resolve()
    files = sorted(
        path
        for path in root.iterdir()
        if path.is_file() and path.resolve() != output_resolved
    )
    if not files:
        raise SystemExit(f"no files found in {root}")

    lines = [f"{sha256(path)}  {path.name}" for path in files]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate SHA256SUMS for release artifacts.")
    parser.add_argument("directory", help="Directory containing release artifacts.")
    parser.add_argument(
        "--output",
        default="SHA256SUMS",
        help="Output path. Relative paths are resolved inside the artifact directory.",
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    main()
