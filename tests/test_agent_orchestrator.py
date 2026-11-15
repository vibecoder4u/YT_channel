import json
import tempfile
import unittest
from pathlib import Path
from agent_orchestrator import DemoAgent, Orchestrator, ROLES

class AgentOrchestratorTests(unittest.TestCase):
    def test_full_dag_succeeds_and_preserves_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = "Do not rewrite this narration.\nSecond line."
            result = Orchestrator(Path(tmp), {r:DemoAgent(r) for r in ROLES}, workers=4).run(script)
            self.assertEqual(result["status"], "succeeded")
            self.assertEqual(result["script"], script)
            self.assertEqual(set(result["tasks"]), {"director","shots","characters","assets","camera","animation","quality","composer"})
            self.assertEqual(result["tasks"]["animation"]["result"]["consumed"], ["assets","camera","characters"])
            self.assertEqual(result["tasks"]["composer"]["result"]["consumed"], ["quality"])

    def test_manifest_is_auditable(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = Orchestrator(Path(tmp), {r:DemoAgent(r) for r in ROLES}).run("unchanged")
            path = Path(tmp) / result["job_id"] / "job_manifest.json"
            saved = json.loads(path.read_text())
            self.assertEqual(saved["status"], "succeeded")
            self.assertGreaterEqual(len(saved["events"]), 16)
            self.assertTrue(all(t["status"] == "succeeded" for t in saved["tasks"].values()))

    def test_missing_agent_fails_fast(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "No worker configured"):
                Orchestrator(Path(tmp), {"director":DemoAgent("director")}).run("script")

    def test_failure_blocks_only_dependents(self):
        class Broken(DemoAgent):
            def run(self, context_path, output_path):
                if self.role == "assets":
                    raise RuntimeError("asset provider unavailable")
                return super().run(context_path, output_path)
        with tempfile.TemporaryDirectory() as tmp:
            agents = {r:Broken(r) for r in ROLES}
            result = Orchestrator(Path(tmp), agents, workers=4, retries=0).run("script")
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["tasks"]["assets"]["status"], "failed")
            self.assertEqual(result["tasks"]["animation"]["status"], "blocked")
            self.assertEqual(result["tasks"]["composer"]["status"], "blocked")
            self.assertEqual(result["tasks"]["camera"]["status"], "succeeded")

if __name__ == "__main__":
    unittest.main()
