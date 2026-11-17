# Self-improving Python Coding Agent (beginner project)

A small **self-correcting** coding agent: generate Python code, run assertion tests, inspect failures, retry, and persist successful solutions to JSON. The demo model is deliberately deterministic, so it works without API keys.

## Requirements

Python 3.10+; no third-party dependencies for demo mode.

## Run

```bash
python main.py --model demo
python -m unittest discover -s tests -v
```

Optional real LLM (requires network and an OpenAI API key):

```bash
export OPENAI_API_KEY="your-key"  # PowerShell: $env:OPENAI_API_KEY="your-key"
python main.py --model openai
```

To change the coding challenge, create another JSON file with `name`, `prompt`, and `tests`, then run `python main.py --model openai --task tasks/your_task.json`. Demo mode only supports the included `clamp` task.

## Architecture

`main.py` loads a task → `CodingAgent` asks a model for code → `run_tests` executes candidate and assertions in a temporary directory → feedback goes to the model → successful code is saved to `memory.json`.

## Safety

**The local subprocess is not a security sandbox.** `-I`, a temporary directory, and a timeout do not prevent generated code from reading files, accessing the network, or spawning processes. Only run demo code or trusted candidate code locally. For real model-generated code, run the *entire agent* inside a disposable container or VM with no network, no secrets, non-root user, read-only filesystem where practical, and CPU/memory/process limits. Never mount your home directory or Docker socket. The optional OpenAI model needs network access to call its API, so a production design should separate the networked model caller from the isolated code executor.

## Portfolio upgrade ideas

- Evaluate on a fixed suite of unseen tasks and record success rate, attempts, latency, and cost.
- Add a Docker-isolated executor with resource limits.
- Store task features and retrieve relevant successful strategies rather than reusing a solution by task name.
- Compare performance with and without memory on a held-out evaluation set.

**Terminology:** this project demonstrates self-correction and persistent solution memory, not model-weight training or proven general learning.
