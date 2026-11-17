import json
import tempfile
import unittest
from pathlib import Path
from agent.core import CodingAgent, DemoModel, Task, run_tests

TASK = Task("clamp", "Implement clamp", "from solution import clamp\nassert clamp(-1,0,10)==0\nassert clamp(12,0,10)==10\n")


class AgentTests(unittest.TestCase):
    def test_failing_code_is_detected(self):
        passed, _ = run_tests("def clamp(value, low, high): return min(value, high)\n", TASK.tests)
        self.assertFalse(passed)

    def test_valid_code_passes(self):
        passed, _ = run_tests("def clamp(value, low, high): return max(low, min(value, high))\n", TASK.tests)
        self.assertTrue(passed)

    def test_agent_repairs_and_remembers(self):
        with tempfile.TemporaryDirectory() as folder:
            memory = Path(folder) / "memory.json"
            self.assertTrue(CodingAgent(DemoModel(), memory).run(TASK))
            self.assertIn("clamp", json.loads(memory.read_text()))
            self.assertTrue(CodingAgent(DemoModel(), memory, max_attempts=1).run(TASK))

    def test_retry_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            memory = Path(folder) / "memory.json"
            self.assertFalse(CodingAgent(DemoModel(), memory, max_attempts=1).run(TASK))
            self.assertFalse(memory.exists())

    def test_timeout(self):
        passed, output = run_tests("while True: pass\n", "import solution\n", timeout=1)
        self.assertFalse(passed)
        self.assertIn("timeout", output)


if __name__ == "__main__":
    unittest.main()
