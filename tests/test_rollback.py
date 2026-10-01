import tempfile
import unittest
from pathlib import Path

from scripts import update_release


class RollbackTests(unittest.TestCase):
    def test_rollback_moves_active_pointer_back_to_previous_version(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            install_root = root / "install"

            for version in ("0.1.0", "0.1.1"):
                source_dir = root / f"incoming-{version}"
                source_dir.mkdir()
                (source_dir / "launcher.py").write_text(f"print('{version}')\n", encoding="utf-8")
                (source_dir / "version.py").write_text(f'__version__ = "{version}"\n', encoding="utf-8")
                update_release.install_release(source_dir, install_root)

            update_release.rollback_release(install_root)

            status = update_release.read_status(install_root)
            self.assertEqual(status["active_version"], "0.1.0")
            self.assertTrue((install_root / "releases" / "0.1.1").is_dir())
            self.assertTrue((install_root / "releases" / "0.1.0").is_dir())

    def test_rollback_requires_previous_release(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            install_root = root / "install"
            source_dir = root / "incoming-0.1.0"
            source_dir.mkdir()
            (source_dir / "launcher.py").write_text("print('ok')\n", encoding="utf-8")
            (source_dir / "version.py").write_text('__version__ = "0.1.0"\n', encoding="utf-8")
            update_release.install_release(source_dir, install_root)

            with self.assertRaises(FileNotFoundError):
                update_release.rollback_release(install_root)


if __name__ == "__main__":
    unittest.main()
