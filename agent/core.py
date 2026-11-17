"""A small coding agent with tests, bounded retries and persistent memory."""
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Task:
    name: str
    prompt: str
    tests: str


class DemoModel:
    """Predictable offline model for teaching the repair loop."""
    def generate(self, task: Task, feedback: str, previous: str, hint: str) -> str:
        if task.name != "clamp":
            raise ValueError("DemoModel only supports the clamp example")
        if hint and not feedback:
            return hint
        if "FAILED" in feedback or "AssertionError" in feedback:
            return "def clamp(value, low, high):\n    return max(low, min(value, high))\n"
        return "def clamp(value, low, high):\n    return min(value, high)\n"  # deliberate bug


class OpenAIModel:
    """Optional real model using the OpenAI Responses API (stdlib HTTP)."""
    def __init__(self, model: str = "gpt-4.1-mini"):
        self.model = model
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("Set OPENAI_API_KEY to use --model openai")

    def generate(self, task: Task, feedback: str, previous: str, hint: str) -> str:
        prompt = (f"Task: {task.prompt}\n\nTests:\n{task.tests}\n\n"
                  f"Prior solution:\n{previous}\n\nTest feedback:\n{feedback}\n\n"
                  f"Previously successful related code:\n{hint}\n\n"
                  "Return only valid Python source code. No Markdown fences. "
                  "Implement the function required by the tests.")
        payload = json.dumps({"model": self.model, "instructions": "You are a Python coding assistant.",
                              "input": prompt}).encode()
        req = urllib.request.Request("https://api.openai.com/v1/responses", data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=40) as response:
            data = json.load(response)
        output = "".join(item.get("text", "") for msg in data.get("output", [])
                         for item in msg.get("content", []) if item.get("type") == "output_text")
        if not output:
            raise RuntimeError("Model returned no text")
        return output.strip().removeprefix("```python").removeprefix("```").removesuffix("```").strip() + "\n"


def run_tests(code: str, tests: str, timeout: int = 5) -> tuple[bool, str]:
    """Execute candidate and tests in a temporary directory. NOT a security sandbox."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder)
        (path / "solution.py").write_text(code, encoding="utf-8")
        (path / "test_solution.py").write_text(tests, encoding="utf-8")
        try:
            result = subprocess.run([sys.executable, "-I", "-c", "import sys,runpy;sys.path.insert(0, '.');runpy.run_path('test_solution.py', run_name='__main__')"],
                cwd=path, capture_output=True, text=True, timeout=timeout,
                env={"PYTHONDONTWRITEBYTECODE": "1"})
        except subprocess.TimeoutExpired:
            return False, f"FAILED: tests exceeded {timeout}s timeout"
        output = (result.stdout + result.stderr)[-3000:]
        return result.returncode == 0, output or ("PASS" if result.returncode == 0 else "FAILED")


class CodingAgent:
    def __init__(self, model, memory_path: Path, max_attempts: int = 3):
        self.model = model
        self.memory_path = memory_path
        self.max_attempts = max_attempts

    def run(self, task: Task) -> bool:
        memory = json.loads(self.memory_path.read_text()) if self.memory_path.exists() else {}
        hint = memory.get(task.name, "")
        previous = ""
        feedback = ""
        for attempt in range(1, self.max_attempts + 1):
            print(f"[attempt {attempt}/{self.max_attempts}] Generating solution...")
            code = self.model.generate(task, feedback, previous, hint)
            passed, feedback = run_tests(code, task.tests)
            print(f"  {'PASS' if passed else 'FAIL'}: {feedback.strip().splitlines()[-1]}")
            if passed:
                memory[task.name] = code
                self.memory_path.parent.mkdir(parents=True, exist_ok=True)
                self.memory_path.write_text(json.dumps(memory, indent=2) + "\n")
                print(f"  Saved successful solution to {self.memory_path}")
                return True
            previous = code
        print("  Stopped: retry budget exhausted")
        return False
