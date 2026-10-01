import tarfile
import tempfile
import unittest
from pathlib import Path

from scripts.package_release import build_release


class ReleasePackageTests(unittest.TestCase):
    def test_release_package_includes_systemd_service(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            archive_path, _ = build_release("0.1.0", output_dir)

            with tarfile.open(archive_path, "r:gz") as archive:
                names = archive.getnames()

            self.assertIn("pi-tv-launcher-v0.1.0/launcher.service", names)


if __name__ == "__main__":
    unittest.main()
