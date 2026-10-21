import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLI = REPO / "aidam.py"


class AidamTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aidam space ")
        self.base = Path(self.temp.name)
        self.workspace = self.base / "My Workspace"

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(CLI), *map(str, args)],
                                capture_output=True, text=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def init(self):
        self.run_cli("init", self.workspace)

    def test_init_then_doctor_in_path_with_spaces(self):
        self.init()
        result = self.run_cli("doctor", self.workspace)
        self.assertIn("ERROR=0", result.stdout)
        self.assertTrue((self.workspace / "active/clients").is_dir())
        self.assertIn("system/AIDAM.md", (self.workspace / "AGENTS.md").read_text())
        self.assertEqual(json.loads((self.workspace / "system/local.json").read_text())["bridges"], {})

    def test_init_refuses_existing_data_without_overwriting(self):
        self.workspace.mkdir()
        note = self.workspace / "my-note.md"
        note.write_text("keep me")
        self.run_cli("init", self.workspace, ok=False)
        self.assertEqual(note.read_text(), "keep me")

    def test_init_cannot_repeat(self):
        self.init()
        self.run_cli("init", self.workspace, ok=False)

    def test_project_and_session_workflow(self):
        self.init()
        self.run_cli("project", self.workspace, "--area", "projects", "--name", "Demo")
        path = self.workspace / "active/projects/Demo"
        self.assertTrue((path / ".context.md").is_file())
        start = self.run_cli("session", "start", self.workspace, "--entry", "codex", "--claim", "active/projects/Demo")
        sid = json.loads(start.stdout)["id"]
        self.run_cli("session", "finish", self.workspace, "--id", sid,
                     "--summary", "演练完成；未连接外部服务")
        logs = list((self.workspace / "system/memory/sessions").rglob("*.md"))
        self.assertEqual(len(logs), 1)
        self.assertIn("[codex]", logs[0].read_text())
        self.assertEqual(json.loads((self.workspace / "system/runtime/sessions.json").read_text()), {})

    def test_claim_overlap_rejected(self):
        self.init()
        self.run_cli("session", "start", self.workspace, "--entry", "codex", "--claim", "active/projects/Demo")
        self.run_cli("session", "start", self.workspace, "--entry", "workbuddy", "--claim", "active/projects/Demo/sub", ok=False)

    def test_nonoverlapping_claims_allowed(self):
        self.init()
        for path in ("active/projects/A", "active/projects/B"):
            self.run_cli("session", "start", self.workspace, "--entry", "codex", "--claim", path)

    def test_path_escape_rejected(self):
        self.init()
        self.run_cli("project", self.workspace, "--area", "projects", "--name", "../../escape", ok=False)
        self.run_cli("session", "start", self.workspace, "--entry", "codex", "--claim", "../outside", ok=False)

    def test_symlink_claim_escape_rejected(self):
        self.init()
        (self.workspace / "active/projects/out").symlink_to(self.base, target_is_directory=True)
        self.run_cli("session", "start", self.workspace, "--entry", "codex", "--claim", "active/projects/out/secret", ok=False)

    def test_doctor_fails_missing_policy(self):
        self.init()
        (self.workspace / "system/AIDAM.md").unlink()
        self.run_cli("doctor", self.workspace, ok=False)

    def copy_release(self):
        import shutil
        target = self.base / "release"
        target.mkdir()
        for name in json.loads((REPO / "share-manifest.json").read_text())["files"]:
            dst = target / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / name, dst)
        shutil.copyfile(REPO / "share-manifest.json", target / "share-manifest.json")
        return target

    def test_share_export_has_only_manifest_files(self):
        release = self.copy_release()
        (release / "private.md").write_text("excluded personal note")
        output = self.base / "aidam.zip"
        self.run_cli("share", "--source", release, "--output", output)
        allowed = json.loads((release / "share-manifest.json").read_text())["files"]
        with zipfile.ZipFile(output) as package:
            self.assertEqual(set(package.namelist()), set(allowed) | {"share-manifest.json", "CHECKSUMS.sha256"})
            self.assertNotIn("private.md", package.namelist())

    def test_share_refuses_symlink(self):
        release = self.copy_release()
        policy = release / "README.md"
        policy.unlink()
        policy.symlink_to(REPO / "README.md")
        self.run_cli("share", "--source", release, "--output", self.base / "out.zip", ok=False)

    def test_share_refuses_credential_pattern_without_echoing_secret(self):
        release = self.copy_release()
        secret = "ghp_" + "Z" * 36
        with (release / "README.md").open("a") as file:
            file.write("\n" + secret)
        result = self.run_cli("share", "--source", release, "--output", self.base / "out.zip", ok=False)
        self.assertNotIn(secret, result.stdout + result.stderr)
        self.assertFalse((self.base / "out.zip").exists())

    def test_share_refuses_modified_manifest(self):
        release = self.copy_release()
        manifest = release / "share-manifest.json"
        data = json.loads(manifest.read_text())
        data["files"].append("system/memory/MEMORY.md")
        manifest.write_text(json.dumps(data))
        self.run_cli("share", "--source", release, "--output", self.base / "out.zip", ok=False)

    def test_share_does_not_overwrite_existing_archive(self):
        release = self.copy_release()
        output = self.base / "out.zip"
        output.write_text("keep")
        self.run_cli("share", "--source", release, "--output", output, ok=False)
        self.assertEqual(output.read_text(), "keep")

    def test_recent_reports_summary_limit_and_is_read_only(self):
        self.init()
        from datetime import datetime
        folder = self.workspace / "system/memory/sessions" / datetime.now().astimezone().strftime("%Y-%m-%d")
        folder.mkdir(parents=True, exist_ok=True)
        for index in range(2):
            (folder / (str(index) + ".md")).write_text("# [codex] 会话记录\n\n验证通过；待补样本", encoding="utf-8")
        before = {p: p.read_bytes() for p in self.workspace.rglob("*") if p.is_file()}
        data = json.loads(self.run_cli("context", "recent", self.workspace, "--limit", "1").stdout)
        self.assertEqual(data["total"], 2)
        self.assertTrue(data["truncated"])
        self.assertIn("待补样本", data["records"][0]["summary"])
        after = {p: p.read_bytes() for p in self.workspace.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_recent_excludes_old_future_and_invalid_dates(self):
        self.init()
        for day in ("2000-01-01", "2999-01-01", "not-a-date"):
            folder = self.workspace / "system/memory/sessions" / day
            folder.mkdir(parents=True)
            (folder / "note.md").write_text("excluded")
        data = json.loads(self.run_cli("context", "recent", self.workspace).stdout)
        self.assertEqual(data["total"], 0)
        self.run_cli("context", "recent", self.workspace, "--days", "0", ok=False)

    def test_assemble_returns_all_candidates_and_no_match(self):
        self.init()
        for name in ("物流甲", "物流乙"):
            self.run_cli("project", self.workspace, "--area", "clients", "--name", name)
        data = json.loads(self.run_cli("context", "assemble", self.workspace, "--task", "物流").stdout)
        self.assertEqual(data["total"], 2)
        self.assertEqual(set(data["records"][0]), {"path"})
        none = json.loads(self.run_cli("context", "assemble", self.workspace, "--task", "不存在").stdout)
        self.assertEqual(none["records"], [])
        self.run_cli("context", "assemble", self.workspace, "--task", " ", ok=False)

    def test_context_rejects_symlink_escape(self):
        self.init()
        outside = self.base / "outside.md"
        outside.write_text("private data")
        self.run_cli("project", self.workspace, "--area", "clients", "--name", "Demo")
        target = self.workspace / "active/clients/Demo/.context.md"
        target.unlink()
        target.symlink_to(outside)
        result = self.run_cli("context", "assemble", self.workspace, "--task", "Demo", ok=False)
        self.assertNotIn("private data", result.stdout + result.stderr)

    def test_clean_share_can_initialize_and_use_installed_context(self):
        archive = self.base / "share.zip"
        self.run_cli("share", "--output", archive)
        unpack = self.base / "unpacked"
        with zipfile.ZipFile(archive) as package:
            package.extractall(unpack)
        subprocess.run([sys.executable, str(unpack / "aidam.py"), "init", str(self.workspace)], check=True, capture_output=True)
        installed = self.workspace / "system/tools/aidam.py"
        for args in (("doctor",), ("context", "recent")):
            result = subprocess.run([sys.executable, str(installed), *args, str(self.workspace)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.workspace / "system/skills/ceo").exists())
        self.assertEqual(json.loads((self.workspace / "system/local.json").read_text())["version"], "0.2.0")


if __name__ == "__main__":
    unittest.main()
