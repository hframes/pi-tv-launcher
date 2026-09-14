#!/usr/bin/env python3

import argparse
import hashlib
import re
import shutil
import sys
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "version.py"
TAG_PATTERN = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
VERSION_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-dev(?:\.\d+)?)?$")


def read_version() -> str:
    namespace = {}
    exec(VERSION_FILE.read_text(encoding="utf-8"), namespace)
    return namespace["__version__"]


def validate_version(version: str) -> None:
    if VERSION_PATTERN.fullmatch(version) is None:
        raise ValueError(f"Invalid application version: {version}")


def validate_tag(version: str, tag: str) -> None:
    if TAG_PATTERN.fullmatch(tag) is None:
        raise ValueError(f"Invalid release tag: {tag}")

    official_version = tag[1:]
    if official_version != version:
        raise ValueError(
            f"Release tag {tag} does not match application version {version}"
        )

    if "-dev" in version:
        raise ValueError(
            f"Official release tags must use a stable application version: {version}"
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_release(version: str, output_dir: Path) -> tuple[Path, Path]:
    package_name = f"pi-tv-launcher-v{version}"
    staging_dir = output_dir / package_name

    if staging_dir.exists():
        shutil.rmtree(staging_dir)

    staging_dir.mkdir(parents=True, exist_ok=True)

    for relative_path in ("launcher.py", "version.py", "README.md", "assets"):
        source_path = ROOT / relative_path
        if not source_path.exists():
            raise FileNotFoundError(f"Required release item is missing: {source_path}")

        destination_path = staging_dir / relative_path
        if source_path.is_dir():
            shutil.copytree(source_path, destination_path)
        else:
            shutil.copy2(source_path, destination_path)

    archive_path = output_dir / f"{package_name}.tar.gz"
    with tarfile.open(archive_path, "w:gz", format=tarfile.PAX_FORMAT) as archive:
        archive.add(staging_dir, arcname=package_name)

    checksum_path = output_dir / f"{archive_path.name}.sha256"
    checksum = sha256_file(archive_path)
    checksum_path.write_text(f"{checksum}  {archive_path.name}\n", encoding="utf-8")

    return archive_path, checksum_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package an official Raspberry Pi release from a version tag."
    )
    parser.add_argument(
        "tag",
        help="Official release tag such as v0.1.0",
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "dist"),
        help="Directory to write the release archive and checksum into.",
    )
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        version = read_version()
        validate_version(version)
        validate_tag(version, args.tag)

        output_dir = Path(args.output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        archive_path, checksum_path = build_release(version, output_dir)

        print(f"Release package created for {args.tag}")
        print(f"Archive: {archive_path}")
        print(f"Checksum: {checksum_path}")
        return 0

    except (FileNotFoundError, OSError, SyntaxError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
