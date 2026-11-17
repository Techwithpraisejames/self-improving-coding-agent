"""Run the coding agent: python main.py [--model demo|openai]."""
import argparse
import json
from pathlib import Path
from agent.core import CodingAgent, DemoModel, OpenAIModel, Task


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["demo", "openai"], default="demo")
    parser.add_argument("--task", type=Path, default=Path("tasks/clamp.json"))
    parser.add_argument("--memory", type=Path, default=Path("memory.json"))
    parser.add_argument("--attempts", type=int, default=3)
    args = parser.parse_args()
    if args.attempts < 1:
        parser.error("--attempts must be at least 1")
    data = json.loads(args.task.read_text())
    task = Task(**data)
    model = DemoModel() if args.model == "demo" else OpenAIModel()
    print(f"Task: {task.name} | Model: {args.model}")
    success = CodingAgent(model, args.memory, args.attempts).run(task)
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
