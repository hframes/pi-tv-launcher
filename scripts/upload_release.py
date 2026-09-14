#!/usr/bin/env python3

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SCRIPT = ROOT / "scripts" / "package_release.py"
DIST_DIR = ROOT / "dist"


def run_command(arguments: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=ROOT,
        text=True,
        check=check,
        capture_output=True,
    )


def repository_name() -> str:
    try:
        remote_url = run_command(["git", "remote", "get-url", "origin"]).stdout.strip()
    except subprocess.CalledProcessError as error:
        raise RuntimeError("Unable to determine the GitHub repository from the git remote.") from error

    remote_url = remote_url.removesuffix(".git")

    for prefix in ("git@github.com:", "ssh://git@github.com/", "https://github.com/"):
        if remote_url.startswith(prefix):
            return remote_url[len(prefix):]

    raise RuntimeError(
        "The origin remote must be a GitHub repository URL in the form "
        "git@github.com:owner/repo or https://github.com/owner/repo."
    )


def release_files(tag: str) -> tuple[Path, Path]:
    version = tag[1:]
    archive_name = f"pi-tv-launcher-{tag}.tar.gz"
    checksum_name = f"{archive_name}.sha256"
    archive_path = DIST_DIR / archive_name
    checksum_path = DIST_DIR / checksum_name

    if not archive_path.exists() or not checksum_path.exists():
        raise FileNotFoundError(
            f"Missing release artifacts for {tag}. Run the package script first."
        )

    return archive_path, checksum_path


def ensure_gh() -> None:
    result = subprocess.run(
        ["gh", "--version"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "GitHub CLI (gh) is required to upload release assets. "
            "Install it and authenticate with 'gh auth login'."
        )


def build_release(tag: str) -> None:
    result = run_command([sys.executable, str(PACKAGE_SCRIPT), tag])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Release packaging failed.")


def create_or_update_release(tag: str, repo: str) -> None:
    result = run_command(["gh", "release", "view", tag, "--repo", repo], check=False)
    if result.returncode == 0:
        return

    run_command([
        "gh",
        "release",
        "create",
        tag,
        "--repo",
        repo,
        "--title",
        f"Release {tag}",
        "--generate-notes",
    ])


def upload_release_assets(tag: str, repo: str) -> None:
    archive_path, checksum_path = release_files(tag)
    run_command([
        "gh",
        "release",
        "upload",
        tag,
        str(archive_path),
        str(checksum_path),
        "--repo",
        repo,
        "--clobber",
    ])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and upload a tagged Raspberry Pi release to GitHub."
    )
    parser.add_argument("tag", help="Official release tag such as v0.1.0")
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Upload existing dist artifacts without rebuilding them.",
    )
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        ensure_gh()

        if not args.skip_build:
            build_release(args.tag)

        repo = repository_name()
        create_or_update_release(args.tag, repo)
        upload_release_assets(args.tag, repo)

        print(f"Uploaded release artifacts for {args.tag} to {repo}")
        return 0

    except (RuntimeError, FileNotFoundError, subprocess.CalledProcessError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
