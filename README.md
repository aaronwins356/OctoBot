# AI Republic

AI Republic is a research-grade governance framework for orchestrating sandboxed entrepreneur agents under a strict legal regime. The system demonstrates how an audited government (the orchestrator) can coordinate semi-autonomous agents while preserving human control, auditability, and safety. All code is local-only; no external network calls are required for core functionality.

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Safety Guarantees](#safety-guarantees)
- [Quick Start](#quick-start)
- [Running the Government](#running-the-government)
- [Creating New Entrepreneurs](#creating-new-entrepreneurs)
- [Proposal Review & Manual Merge](#proposal-review--manual-merge)
- [Audit Logs & Memory](#audit-logs--memory)
- [Maintaining the Laws](#maintaining-the-laws)
- [Testing & CI](#testing--ci)
- [License](#license)

## Architecture Overview
The repository is organised into distinct domains:

- `laws/` — Contains the constitution, validators, audit utilities, and enforcement APIs. These files are immutable at runtime and define the binding policy for the entire system.
- `government/` — Implements discovery, sandbox management, proposal handling, and orchestrator logic. It registers agents, enforces the laws, and records economic credits.
- `entrepreneurs/` — Houses BaseAgent subclasses. Each agent is sandboxed inside `sandbox/agents/<agent_name>/` and interacts with the government via structured messages.
- `memory/` — Provides an SQLite-backed log, retrieval functions, and offline reflections (stored in `logs/reflections/`).
- `economy/` — Maintains a strictly simulated ledger used to award credits for useful work.
- `sandbox/` — Contains run directories for agents and a `proposals/` folder where agents deposit drafts for human review.
- `interface/` — A CLI tool for human reviewers to inspect proposals and drive the approval process.
- `docs/` — Additional documentation including architecture diagrams and human approval checklists.

A high-level flow is illustrated in `docs/ARCHITECTURE.md`.

## Safety Guarantees
1. **Immutable Laws:** Files under `laws/` are considered read-only during runtime. Agents may call enforcement helper APIs but cannot change or bypass them.
2. **Sandboxed Execution:** Agents execute in isolated subprocesses with explicit working directories and resource limits. Dry-run mode performs only static validation.
3. **AST-Based Validation:** The government inspects agent source code using Python's `ast` module to prevent disallowed imports, subprocess calls, or filesystem access outside the sandbox.
4. **Audit Trail:** Every agent run is logged with a tamper-evident SHA256 hash, timestamp, and enforcement version. Logs are stored under `logs/` and in the SQLite memory database.
5. **Human-in-the-Loop:** Proposal creation requires human approval. The orchestrator drafts pull requests but never merges them. The CLI outputs exact git commands for manual review.
6. **Offline Friendly:** All components function without network access. Optional GitHub integration activates only when `GITHUB_TOKEN` is set.

## Quick Start
1. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. **Populate environment variables**
   - Copy `.env.example` to `.env` (optional).
   - Set `OFFLINE_MODE=true` by default to avoid network calls.

3. **Initialize directories** (done automatically in the repo) but ensure `logs/` and `sandbox/` are writable.

## Running the Government
### Dry Run (recommended)
```
make run
```
This executes `government/orchestrator.py` in dry-run mode, performing discovery, validation, and simulations without running agent code.

### Live Run (safe mode)
```
python -m government.orchestrator --live
```
Live mode launches agents inside subprocesses with enforced sandboxes. All actions remain local and auditable.

## Creating New Entrepreneurs
1. **Create a new module** in `entrepreneurs/` implementing `BaseAgent`.
2. **Declare a sandbox** by using `government.sandbox.SandboxPaths.create("agent_name")`.
3. **Implement `setup`, `run`, and `report`**. Use pydantic models to structure outputs.
4. **Ensure compliance** by running `python -m laws.enforcement <agent_path>` (optional helper) or rely on the orchestrator's validation.
5. **Register** — The government automatically discovers agents under `entrepreneurs/`.

## Proposal Review & Manual Merge
Agents may output proposals that the orchestrator packages into `sandbox/proposals/<timestamp>_<agent>/`. Use the CLI to inspect:

```bash
brain list-proposals
brain show-proposal <proposal_id>
brain run-proposal-tests <proposal_id>
brain approve-proposal <proposal_id>
```

`approve-proposal` prints the exact git commands to create a branch, apply the proposal patch, push, and open a PR. The orchestrator itself creates draft PRs only if `GITHUB_TOKEN` is configured and never merges automatically.

## Audit Logs & Memory
- Logs live in `logs/` with rotation and tamper-evident hashes produced by `laws.audit`.
- Short-term memory is stored in `memory/data/state.db`. Use `memory.__init__.py` functions `store_event`, `query_recent`, and `summarize_recent` for interactions.
- Reflection reports are periodically generated and saved to `logs/reflections/`.

## Maintaining the Laws
The `laws/` folder is versioned and immutable at runtime. Any modification requires a human-authored commit reviewed by maintainers. Agents do not have the capability to load or mutate these modules beyond invoking published APIs.

## Testing & CI
- Run `make lint` to execute Ruff static analysis.
- Run `make test` to execute the pytest suite.
- GitHub Actions workflow `.github/workflows/ci.yml` runs both linting and tests. Branch protection rules (configure in GitHub) must require passing CI and at least two human approvals before merge.

## License
This project is provided for research and observation. Use responsibly and ensure human oversight for any real-world deployment.
