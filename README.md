# Pi TV Launcher

A simple fullscreen launcher for starting streaming services on a Raspberry Pi.

## Versioning

The application version is defined once in [version.py](version.py).

Versions use this format:

- Development: `MAJOR.MINOR.PATCH-dev` or `MAJOR.MINOR.PATCH-dev.N`
- Official release: `MAJOR.MINOR.PATCH`
- Official Git tags add a `v` prefix, for example `v0.1.0`

Validate the current development version with:

```bash
python3 scripts/validate_version.py
```

Validate an official release tag against the application version with:

```bash
python3 scripts/validate_version.py v0.1.0
```

## Creating a release

1. Change `__version__` in `version.py` to the intended stable version.
2. Validate the version and release tag:

   ```bash
   python3 scripts/validate_version.py v0.1.0
   ```

3. Commit the version change.
4. Create and push the matching tag:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

5. Build an official release package from that tag:

   ```bash
   python3 scripts/package_release.py v0.1.0
   ```

   This creates a tar.gz archive in the `dist/` directory together with a matching `.sha256` checksum file.

6. Upload the package and checksum to the GitHub release:

   ```bash
   ./scripts/upload_release.py v0.1.0
   ```

   The helper builds the release package if needed, creates the GitHub release if it does not exist, and uploads both artifacts.

7. Verify the downloaded package before installing it:

   ```bash
   cd dist
   sha256sum -c pi-tv-launcher-v0.1.0.tar.gz.sha256
   ```

## Release artifact contents

The packaging step creates a versioned archive and checksum in `dist/`:

- `pi-tv-launcher-v0.1.0.tar.gz`
- `pi-tv-launcher-v0.1.0.tar.gz.sha256`

The archive contains the runtime payload for the Raspberry Pi:

- `launcher.py`
- `launcher.service`
- `version.py`
- `README.md`
- `assets/`

This keeps the published release self-contained and verifiable before installation.

## Raspberry Pi startup service

The packaged release includes a systemd unit file, `launcher.service`, for starting the launcher automatically after the graphical environment is available.

Install the service on the Pi as follows:

```bash
sudo mkdir -p /opt/pi-tv-launcher
sudo tar -xzf pi-tv-launcher-v0.1.0.tar.gz -C /opt
sudo cp /opt/pi-tv-launcher-v0.1.0/launcher.service /etc/systemd/system/pi-tv-launcher.service
sudo systemctl daemon-reload
sudo systemctl enable --now pi-tv-launcher.service
sudo systemctl status pi-tv-launcher.service
```

The launcher runs as the `pi` user, with `DISPLAY=:0` and `XAUTHORITY=/home/pi/.Xauthority` configured so it can open the desktop session. The service uses `Restart=on-failure` and logs to the journal, making it easy to diagnose startup problems.

Useful administration commands:

```bash
sudo systemctl start pi-tv-launcher.service
sudo systemctl stop pi-tv-launcher.service
sudo systemctl restart pi-tv-launcher.service
sudo systemctl disable --now pi-tv-launcher.service
journalctl -u pi-tv-launcher.service -f
```

## Checking for a release update

The project includes a lightweight updater script that checks the latest GitHub release, downloads the archive to a temporary staging directory, verifies the checksum, and reports what it would do in dry-run mode without changing the current installation.

```bash
python3 scripts/update_release.py --dry-run
```

To run the updater against a specific repository or installation target:

```bash
python3 scripts/update_release.py --repo hframes/pi-tv-launcher --dry-run
python3 scripts/update_release.py --repo hframes/pi-tv-launcher --install-dir /opt/pi-tv-launcher
```

The updater fails safely if:

- the GitHub release metadata cannot be read,
- no release is available,
- the checksum does not match the downloaded archive,
- the downloaded artifact is malformed or incomplete.

## Versioned Pi installations

Releases are installed into a versioned directory layout instead of modifying the active installation in place. The update flow keeps the live release stable until a new version is fully staged and activated.

A typical install root looks like this:

```text
/opt/pi-tv-launcher/
├── current -> releases/0.1.1
├── previous -> releases/0.1.0
├── releases/
│   ├── 0.1.0/
│   └── 0.1.1/
├── .update-status.json
└── .staging/
```

The `current` symlink is replaced atomically, so an interrupted or failed installation cannot leave the launcher half-updated. The previous version remains available until the next update, and the active version plus update state can be inspected from the install root:

```bash
readlink /opt/pi-tv-launcher/current
cat /opt/pi-tv-launcher/.update-status.json
```

Development work should keep the `-dev` suffix. The release package and future updater will use official version tags rather than commits from `main`.
