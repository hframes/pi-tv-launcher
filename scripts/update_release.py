#!/usr/bin/env python3

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "version.py"


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


def read_version() -> str:
    namespace = {}
    exec(VERSION_FILE.read_text(encoding="utf-8"), namespace)
    return namespace["__version__"]


def latest_release_tag(repo: str) -> str:
    result = run_command([
        "gh",
        "release",
        "list",
        "--repo",
        repo,
        "--limit",
        "1",
        "--json",
        "tagName",
    ])

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("Unable to parse GitHub release metadata.") from error

    if not payload:
        raise RuntimeError(f"No releases were found for {repo}.")

    tag_name = payload[0].get("tagName")
    if not tag_name:
        raise RuntimeError("GitHub release metadata did not include a tag name.")

    return tag_name


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_archive(archive_path: Path, checksum_path: Path) -> None:
    if not archive_path.exists():
        raise FileNotFoundError(f"Release archive does not exist: {archive_path}")
    if not checksum_path.exists():
        raise FileNotFoundError(f"Checksum file does not exist: {checksum_path}")

    lines = checksum_path.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        raise ValueError(f"Checksum file is empty: {checksum_path}")

    expected = lines[0].split()[0]
    actual = sha256_file(archive_path)

    if actual != expected.lower():
        raise ValueError(
            f"Checksum mismatch for {archive_path.name}: "
            f"expected {expected}, got {actual}"
        )


def download_release(repo: str, tag: str, destination_dir: Path) -> tuple[Path, Path]:
    destination_dir.mkdir(parents=True, exist_ok=True)
    result = run_command([
        "gh",
        "release",
        "download",
        tag,
        "--repo",
        repo,
        "--dir",
        str(destination_dir),
        "--pattern",
        "pi-tv-launcher-*.tar.gz*",
    ])

    archive_candidates = sorted(destination_dir.glob("pi-tv-launcher-*.tar.gz"))
    checksum_candidates = sorted(destination_dir.glob("pi-tv-launcher-*.tar.gz.sha256"))

    if not archive_candidates or not checksum_candidates:
        raise RuntimeError(f"Unable to download the release assets for {tag} from {repo}.")

    archive_path = archive_candidates[0]
    checksum_path = checksum_candidates[0]
    verify_archive(archive_path, checksum_path)
    return archive_path, checksum_path


def extract_release(archive_path: Path, destination_dir: Path) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as archive:
        archive.extractall(destination_dir)

    top_level = sorted(destination_dir.iterdir())
    if not top_level:
        raise RuntimeError(f"Release archive {archive_path} did not contain a package payload.")

    return top_level[0]


def resolve_repo() -> str:
    try:
        return repository_name()
    except RuntimeError:
        return "hframes/pi-tv-launcher"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check the latest GitHub release and stage it without modifying a live installation.",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="GitHub repository in owner/name format. Defaults to the git remote.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report the latest release and the staged install target without changing the live installation.",
    )
    parser.add_argument(
        "--install-dir",
        type=Path,
        default=None,
        help="Optional destination directory for the extracted release when not using dry-run mode.",
    )
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        repo = args.repo or resolve_repo()
        installed_version = read_version()

        latest = latest_release_tag(repo)
        print(f"Installed version: {installed_version}")
        print(f"Latest release: {latest}")

        if args.dry_run:
            print("Dry run: no live installation changes were made.")
            return 0

        if args.install_dir is None:
            raise ValueError("An install directory is required when not using --dry-run.")

        with tempfile.TemporaryDirectory(prefix="pi-tv-launcher-update-") as temp_dir:
            staging_dir = Path(temp_dir)
            archive_path, checksum_path = download_release(repo, latest, staging_dir)
            extraction_dir = staging_dir / "staged-release"
            extracted_path = extract_release(archive_path, extraction_dir)

            install_dir = args.install_dir
            shutil.copytree(extracted_path, install_dir, dirs_exist_ok=True)
            print(f"Release {latest} verified and staged at {install_dir}")
            print(f"Checksum verified: {checksum_path}")
            return 0

    except (RuntimeError, ValueError, FileNotFoundError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
