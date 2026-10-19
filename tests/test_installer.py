"""Run with python3 -m unittest discover -s tests. No network or user config writes."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


INSTALLER = Path(__file__).resolve().parents[1] / "get.sh"


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="justcast-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "commands"
        self.env = {
            **os.environ,
            "PATH": str(self.bin),
            "TMPDIR": str(self.root),
            "INSTALLER_TEST_LOG": str(self.log),
        }
        for name in ("mktemp", "rmdir"):
            (self.bin / name).symlink_to(Path("/usr/bin") / name if
                                         (Path("/usr/bin") / name).exists() else
                                         Path("/bin") / name)
        self.stub("git", "exit 0")
        self.stub("codex", '''
if [[ "$*" == *--help ]]; then
  exit "${TEST_HELP_STATUS:-0}"
fi
echo "$*" >> "$INSTALLER_TEST_LOG"
echo "$PWD" > "$INSTALLER_TEST_LOG.cwd"
if [[ "$*" == 'plugin marketplace add '* ]]; then
  exit "${TEST_MARKETPLACE_STATUS:-0}"
fi
exit "${TEST_INSTALL_STATUS:-0}"
''')

    def stub(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/bash\n" + body + "\n")
        path.chmod(0o755)

    def run_installer(self, *args, piped=False):
        if piped:
            return subprocess.run(
                ["/bin/bash", "-s", "--", *args], input=INSTALLER.read_text(),
                cwd=INSTALLER.parent, env=self.env, capture_output=True, text=True,
            )
        return subprocess.run(
            ["/bin/bash", str(INSTALLER), *args], cwd=INSTALLER.parent,
            env=self.env, capture_output=True, text=True,
        )

    def commands(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def test_piped_install_uses_github_and_cleans_working_directory(self):
        result = self.run_installer(piped=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.commands(), [
            "plugin marketplace add https://github.com/montekaka/justcast-skills.git --ref main",
            "plugin add justcast@justcast",
        ])
        working_dir = Path(Path(str(self.log) + ".cwd").read_text().strip())
        self.assertNotEqual(working_dir, INSTALLER.parent)
        self.assertFalse(working_dir.exists())
        self.assertIn("$justcast:volume-control init", result.stdout)

    def test_missing_dependencies_stop_before_install(self):
        for name in ("codex", "git"):
            with self.subTest(name=name):
                path = self.bin / name
                saved = path.read_text()
                path.unlink()
                result = self.run_installer()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("required", result.stderr)
                self.assertEqual(self.commands(), [])
                self.stub(name, saved)

    def test_unsupported_cli_stops_before_install(self):
        self.env["TEST_HELP_STATUS"] = "2"
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Update Codex CLI", result.stderr)
        self.assertEqual(self.commands(), [])

    def test_failures_stop_and_clean_up(self):
        for stage, count in (("MARKETPLACE", 1), ("INSTALL", 2)):
            with self.subTest(stage=stage):
                self.env["TEST_" + stage + "_STATUS"] = "7"
                result = self.run_installer()
                self.assertEqual(result.returncode, 7, result.stderr)
                self.assertEqual(len(self.commands()), count)
                self.assertNotIn("JustCast is installed", result.stdout)
                self.assertEqual(list(self.root.glob("justcast-install.*")), [])
                self.env.pop("TEST_" + stage + "_STATUS")
                self.log.unlink()

    def test_help_and_invalid_arguments_do_not_install(self):
        self.assertEqual(self.run_installer("--help").returncode, 0)
        self.assertNotEqual(self.run_installer("--unknown").returncode, 0)
        self.assertEqual(self.commands(), [])


if __name__ == "__main__":
    unittest.main()
