#!/usr/bin/env python3

import argparse
import json
import os
import shutil
import socket
import sys
from pathlib import Path


def _has_pillow() -> bool:
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        return False


def evaluate_environment(
    repo_root: Path,
    *,
    display: str | None = None,
    chromium: str | None = None,
    network_host: str = "github.com",
    network_port: int = 443,
) -> dict[str, bool]:
    report = {
        "chromium": bool(chromium) if chromium is not None else shutil.which("chromium") is not None,
        "pillow": _has_pillow(),
        "display": bool(display or os.environ.get("DISPLAY") or Path("/tmp/.X11-unix").exists()),
        "assets": (repo_root / "assets").exists(),
        "network": False,
    }

    try:
        with socket.create_connection((network_host, network_port), timeout=5):
            report["network"] = True
    except OSError:
        report["network"] = False

    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check the Raspberry Pi prerequisites for the first launcher deployment.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root used to confirm required assets are present.",
    )
    parser.add_argument(
        "--display",
        default=None,
        help="Optional DISPLAY value to validate desktop access for the launcher.",
    )
    parser.add_argument(
        "--chromium",
        default=None,
        help="Optional path to the Chromium binary to validate the browser is installed.",
    )
    parser.add_argument(
        "--network-host",
        default="github.com",
        help="Host to probe to confirm outbound network access for release checks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = evaluate_environment(
        args.repo_root,
        display=args.display,
        chromium=args.chromium,
        network_host=args.network_host,
    )
    print(json.dumps(report, indent=2, sort_keys=True))

    required_checks = ("chromium", "pillow", "display", "assets", "network")
    if any(not report[key] for key in required_checks):
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
