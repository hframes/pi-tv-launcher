#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
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


def release_version(release_dir: Path) -> str:
    version_file = release_dir / "version.py"
    if not version_file.exists():
        raise FileNotFoundError(f"Release directory is missing version metadata: {release_dir}")

    namespace = {}
    exec(version_file.read_text(encoding="utf-8"), namespace)
    return str(namespace["__version__"])


def write_status(install_root: Path, *, active_version: str, state: str = "ready") -> None:
    install_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "active_version": active_version,
        "state": state,
    }
    (install_root / ".update-status.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_status(install_root: Path) -> dict[str, str]:
    status_file = install_root / ".update-status.json"
    if status_file.exists():
        return json.loads(status_file.read_text(encoding="utf-8"))

    current_link = install_root / "current"
    if current_link.exists() or current_link.is_symlink():
        active_version = current_link.resolve().name
        return {"active_version": active_version, "state": "ready"}

    return {"active_version": "unknown", "state": "uninitialized"}


def install_release(source_dir: Path, install_root: Path) -> Path:
    install_root.mkdir(parents=True, exist_ok=True)
    version = release_version(source_dir)
    release_dir = install_root / "releases" / version
    releases_dir = install_root / "releases"
    releases_dir.mkdir(parents=True, exist_ok=True)

    if release_dir.exists():
        raise FileExistsError(f"Release {version} is already installed at {release_dir}")

    staging_dir = install_root / ".staging" / version
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    shutil.copytree(source_dir, staging_dir)

    os.replace(staging_dir, release_dir)

    current_link = install_root / "current"
    previous_version = None
    if current_link.exists() or current_link.is_symlink():
        previous_target = current_link.resolve()
        previous_version = previous_target.name if previous_target.exists() else None
        previous_link = install_root / "previous"
        if previous_link.exists() or previous_link.is_symlink():
            previous_link.unlink()
        if previous_version is not None:
            os.symlink(f"releases/{previous_version}", previous_link)

    next_current = install_root / ".current.new"
    if next_current.exists() or next_current.is_symlink():
        next_current.unlink()
    os.symlink(f"releases/{version}", next_current)
    os.replace(next_current, current_link)

    if previous_version is not None:
        retain = {version, previous_version}
    else:
        retain = {version}

    for candidate in sorted(releases_dir.iterdir(), key=lambda item: item.name):
        if candidate.name not in retain and candidate.is_dir():
            shutil.rmtree(candidate)

    write_status(install_root, active_version=version, state="ready")
    return release_dir


def rollback_release(install_root: Path) -> Path:
    install_root.mkdir(parents=True, exist_ok=True)
    previous_link = install_root / "previous"
    if not previous_link.exists() and not previous_link.is_symlink():
        raise FileNotFoundError(f"No previous release exists to roll back to in {install_root}")

    current_link = install_root / "current"
    if not current_link.exists() and not current_link.is_symlink():
        raise FileNotFoundError(f"No active release is installed in {install_root}")

    current_target = current_link.resolve()
    if not current_target.exists():
        raise FileNotFoundError(f"Current release target is missing: {current_target}")

    previous_target = previous_link.resolve()
    if not previous_target.exists():
        raise FileNotFoundError(f"Previous release target is missing: {previous_target}")

    rollback_version = previous_target.name
    next_current = install_root / ".current.new"
    if next_current.exists() or next_current.is_symlink():
        next_current.unlink()
    os.symlink(previous_target.relative_to(install_root), next_current)
    os.replace(next_current, current_link)

    if previous_link.exists() or previous_link.is_symlink():
        previous_link.unlink()
    os.symlink(f"releases/{current_target.name}", previous_link)

    write_status(install_root, active_version=rollback_version, state="rolled_back")
    return install_root / "releases" / rollback_version


def resolve_repo() -> str:
    try:
        return repository_name()
    except RuntimeError:
        return "hframes/pi-tv-launcher"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check the latest GitHub release and install it into a versioned layout without modifying the active pointer in place.",
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
        help="Root directory for versioned releases. The active version is exposed via the current symlink.",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print the active version and update status for the install root.",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Restore the previous known-good release using the previous symlink.",
    )
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        repo = args.repo or resolve_repo()

        if args.status:
            install_root = args.install_dir or Path("/opt/pi-tv-launcher")
            status = read_status(install_root)
            print(json.dumps(status, indent=2, sort_keys=True))
            return 0

        if args.rollback:
            if args.install_dir is None:
                raise ValueError("--install-dir is required when using --rollback.")
            restore_target = rollback_release(args.install_dir)
            print(f"Rolled back to {restore_target.name}")
            print(json.dumps(read_status(args.install_dir), indent=2, sort_keys=True))
            return 0

        installed_version = read_version()
        latest = latest_release_tag(repo)
        print(f"Installed version: {installed_version}")
        print(f"Latest release: {latest}")

        if args.dry_run:
            print("Dry run: no live installation changes were made.")
            return 0

        if args.install_dir is None:
            raise ValueError("An install directory is required when not using --dry-run, --status, or --rollback.")

        with tempfile.TemporaryDirectory(prefix="pi-tv-launcher-update-") as temp_dir:
            staging_dir = Path(temp_dir)
            archive_path, checksum_path = download_release(repo, latest, staging_dir)
            extraction_dir = staging_dir / "staged-release"
            extracted_path = extract_release(archive_path, extraction_dir)

            install_root = args.install_dir
            install_release(extracted_path, install_root)
            print(f"Release {latest} verified and installed under {install_root / 'releases'}")
            print(f"Checksum verified: {checksum_path}")
            print(f"Active version: {read_status(install_root)['active_version']}")
            return 0

    except (RuntimeError, ValueError, FileNotFoundError, subprocess.CalledProcessError, FileExistsError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
