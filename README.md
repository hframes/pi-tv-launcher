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

Development work should keep the `-dev` suffix. The release package and future updater will use official version tags rather than commits from `main`.
