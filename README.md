# OctoBot Governance Platform

OctoBot is a constitutional automation stack that drafts, evaluates, and hardens code changes under
strict human oversight. Every autonomous action is logged, validated against runtime laws, and stored
for later reflection.

## System Architecture

```
┌────────────┐      ┌──────────────┐      ┌────────────┐
│ Engineers  │      │  Orchestrator│      │   Updater  │
│ (Analyzer, │─────▶│  & Evaluator │─────▶│(Dry-run or │
│ Writer,    │      └──────┬───────┘      │  Commit)   │
│ Tester,     │            │              └────┬───────┘
│ Documentor) │            │                   │
└────┬────────┘            │                   │
     │                     ▼                   ▼
     │            ┌──────────────┐      ┌──────────────┐
     │            │ Proposal      │      │ Laws/Validator│
     └───────────▶│ Manager &     │◀────▶│ + Audit       │
                  │ Ledger        │      └──────────────┘
                  └──────┬───────┘
                         ▼
                 ┌──────────────┐
                 │ Interface     │
                 │ (CLI & UI)    │
                 └──────────────┘
```

## Key Capabilities

- **Poetry-first toolchain** with reproducible dependency management and isolated dev/test groups.
- **Constitutional enforcement** via `octobot.laws.validator`, `ethics.yaml`, and `tech_standards.yaml`.
- **Entrepreneur simulations** for trading, blogging, and software ventures under strict guardrails.
- **Structlog telemetry** streamed to `memory/logs/events.jsonl` for weekly reflection digests.
- **FastAPI dashboard** presenting proposal purpose, ROI, risk, and validation results.
- **Nightly documentation regeneration** driven by the documentor agent and GitHub Actions.

## Getting Started

1. Install Poetry 1.8+ and clone the repository.
2. Install dependencies and activate pre-commit hooks:
   ```bash
   poetry install
   poetry run pre-commit install
   ```
3. Regenerate documentation and run the initial analysis:
   ```bash
   poetry run python -m octobot.agents.engineers.documentor_agent
   poetry run octobot propose "Architecture Review"
   ```
4. Inspect the proposal through the CLI or launch the dashboard:
   ```bash
   poetry run octobot status
   poetry run python -m octobot.interface.cli dashboard
   ```

## Docker Environment

The provided Dockerfile builds a lightweight Python 3.11 image, installs Poetry dependencies, mounts
`/workspace`, and starts the CLI status command by default. Use it for reproducible CI or air-gapped
analysis:

```bash
docker build -t octobot .
docker run --rm -it -v "$(pwd)":/workspace octobot poetry run octobot status
```

## Quality Gates

- Pre-commit enforces **black**, **isort**, **flake8**, and **mypy** on every commit.
- GitHub Actions run linting, pytest + coverage (90% threshold), and safety scans on each PR.
- Integration tests cover the full proposal lifecycle (`tests/test_full_cycle.py`).

## Directory Overview

- `octobot/agents/engineers/` – proposal analysis, authoring, documentation, and testing agents.
- `octobot/agents/entrepreneurs/` – trading, blogging, and software venture simulations with plans.
- `octobot/laws/` – constitution, ethics, tech standards, validator, and audit tooling.
- `octobot/memory/` – structlog logger, reflector digests, ledger, and utilities.
- `interface/` – CLI and FastAPI dashboard for human oversight.
- `tests/` – pytest + hypothesis suites by subsystem plus end-to-end coverage.

## Safety & Oversight

- All agents must register with the validator before autonomous execution.
- Proposals remain in `/proposals` until human approval; merges require coverage ≥ 90%.
- Weekly reflection digests summarise successes, failures, and improvement suggestions without
  mutating code.

## Nightly Documentation

The `Documentation Nightly` workflow invokes `octobot.agents.engineers.documentor_agent` to rebuild
`docs/index.md`, `architecture.md`, `laws.md`, and `developer_guide.md` from live docstrings.

For deeper architectural notes consult the regenerated docs under `/docs/`.
