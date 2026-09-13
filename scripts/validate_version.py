#!/usr/bin/env python3

import re
import sys
from pathlib import Path


VERSION_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-dev(?:\.\d+)?)?$")
TAG_PATTERN = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def read_version() -> str:
    version_file = Path(__file__).parents[1] / "version.py"
    namespace = {}
    exec(version_file.read_text(encoding="utf-8"), namespace)
    return namespace["__version__"]


def validate(version: str, tag: str | None = None) -> None:
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"Invalid application version: {version}")

    if tag is None:
        return

    match = TAG_PATTERN.fullmatch(tag)
    if match is None:
        raise ValueError(f"Invalid release tag: {tag}")

    tagged_version = tag[1:]
    if version != tagged_version:
        raise ValueError(
            f"Release tag {tag} does not match application version {version}"
        )


if __name__ == "__main__":
    release_tag = sys.argv[1] if len(sys.argv) == 2 else None
    if len(sys.argv) > 2:
        raise SystemExit("Usage: validate_version.py [vMAJOR.MINOR.PATCH]")

    try:
        application_version = read_version()
        validate(application_version, release_tag)
    except (KeyError, OSError, SyntaxError, ValueError) as error:
        raise SystemExit(str(error)) from error

    print(f"Application version is valid: {application_version}")
