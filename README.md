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

Development work should keep the `-dev` suffix. The release package and future updater will use official version tags rather than commits from `main`.
