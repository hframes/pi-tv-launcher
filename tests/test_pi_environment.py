import tempfile
import unittest
from pathlib import Path

from scripts import check_pi_environment


class PiEnvironmentChecks(unittest.TestCase):
    def test_environment_report_includes_required_checks(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "assets").mkdir()
            report = check_pi_environment.evaluate_environment(repo_root, display=":0", chromium="/usr/bin/chromium")

            self.assertIn("chromium", report)
            self.assertIn("pillow", report)
            self.assertIn("display", report)
            self.assertIn("assets", report)
            self.assertIn("network", report)
            self.assertEqual(report["display"], True)

    def test_missing_chromium_is_reported_as_failure(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "assets").mkdir()
            report = check_pi_environment.evaluate_environment(repo_root, display=":0", chromium="")
            self.assertEqual(report["chromium"], False)


if __name__ == "__main__":
    unittest.main()
