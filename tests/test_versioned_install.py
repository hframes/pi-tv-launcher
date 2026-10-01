import tempfile
import unittest
from pathlib import Path

from scripts import update_release


class VersionedInstallTests(unittest.TestCase):
    def test_install_release_uses_versioned_directory_and_current_pointer(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "incoming"
            source_dir.mkdir()
            (source_dir / "launcher.py").write_text("print('ok')\n", encoding="utf-8")
            (source_dir / "version.py").write_text('__version__ = "0.1.0"\n', encoding="utf-8")

            update_release.install_release(source_dir, root / "install")
            release_dir = root / "install" / "releases" / "0.1.0"
            current_link = root / "install" / "current"

            self.assertTrue(release_dir.is_dir())
            self.assertTrue(current_link.is_symlink())
            self.assertEqual(current_link.resolve(), release_dir)

            status = update_release.read_status(root / "install")
            self.assertEqual(status["active_version"], "0.1.0")
            self.assertEqual(status["state"], "ready")

    def test_install_release_keeps_previous_version_available(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            install_root = root / "install"

            for version in ("0.1.0", "0.1.1"):
                source_dir = root / f"incoming-{version}"
                source_dir.mkdir()
                (source_dir / "launcher.py").write_text(f"print('{version}')\n", encoding="utf-8")
                (source_dir / "version.py").write_text(f'__version__ = "{version}"\n', encoding="utf-8")
                update_release.install_release(source_dir, install_root)

            current_link = install_root / "current"
            self.assertEqual(current_link.resolve(), install_root / "releases" / "0.1.1")
            self.assertTrue((install_root / "releases" / "0.1.0").is_dir())

            status = update_release.read_status(install_root)
            self.assertEqual(status["active_version"], "0.1.1")
            self.assertEqual(status["state"], "ready")


if __name__ == "__main__":
    unittest.main()
