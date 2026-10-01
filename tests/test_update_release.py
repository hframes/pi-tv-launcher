import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import update_release


class UpdateReleaseTests(unittest.TestCase):
    def test_latest_release_tag_uses_github_release_api(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            gh_stub = Path(tmp_dir) / "gh"
            gh_stub.write_text(
                "#!/usr/bin/env python3\n"
                "import json\n"
                "import sys\n"
                "payload = [{\"tagName\": \"v0.2.0\"}]\n"
                "if 'release list' in ' '.join(sys.argv[1:]):\n"
                "    print(json.dumps(payload))\n"
                "else:\n"
                "    raise SystemExit(1)\n",
                encoding="utf-8",
            )
            gh_stub.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{tmp_dir}{os.pathsep}{old_path}"
            try:
                self.assertEqual(update_release.latest_release_tag("demo/repo"), "v0.2.0")
            finally:
                os.environ["PATH"] = old_path

    def test_verify_checksum_rejects_invalid_archive(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            archive = Path(tmp_dir) / "archive.tar.gz"
            archive.write_bytes(b"bad data")
            checksum = Path(tmp_dir) / "archive.tar.gz.sha256"
            checksum.write_text("abc123  archive.tar.gz\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                update_release.verify_archive(archive, checksum)


if __name__ == "__main__":
    unittest.main()
