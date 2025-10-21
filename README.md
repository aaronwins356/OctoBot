# OctoBot: The Self-Improvement Framework

OctoBot is a modular research framework that learns to analyze its own codebase, surface improvement proposals, and queue
changes for human approval. The goal is to demonstrate scalable self-analysis and transparent reasoning for AI software
projects without removing humans from the loop.

## Key Features
- **Human Oversight:** Every proposed change is queued for review and cannot be merged without explicit approval from the
  dashboard.
- **Transparency:** Analyzer reports, generated proposals, risk assessments, and decisions are recorded in natural language
  and stored for auditing.
- **Reproducibility:** All merges are performed through Git commits logged by the updater module after approval.
- **Ethics Guardrails:** YAML constitutions constrain network access, mandate rationale logging, and ensure proposals serve
  human benefit.

## Repository Layout
```
octobot/core/         # Orchestration, proposal management, scoring, merging
octobot/agents/       # Engineer and entrepreneur agents for analysis and innovation
octobot/laws/         # Constitutional documents and validators enforcing compliance
octobot/connectors/   # Interfaces to external systems (Chat Unreal bridge, crawlers)
octobot/interface/    # Human-facing CLI and FastAPI + HTMX dashboard
octobot/memory/       # SQLite persistence, metrics, logging utilities, and ledger
octobot/utils/        # Shared helper utilities
octobot/tests/        # Automated regression tests
proposals/            # Generated proposal packages awaiting review
scripts/              # Helper scripts for bootstrapping and maintenance
docs/                 # Architectural documentation and user guides
```

## Getting Started
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Initialize the database and generate an example proposal:
   ```bash
   python -m octobot.interface.cli propose "Architecture Review"
   ```
3. Launch the dashboard to inspect proposals, laws, and history:
   ```bash
   python -m octobot.interface.cli dashboard
   ```
4. Approve a proposal through the dashboard or CLI (`python -m octobot.interface.cli approve <proposal_id>`). The orchestrator runs tests and applies the change after approval.

## Safety Principles
- **No Unreviewed Execution:** `laws/constitution.yaml` forbids automatic merges without human approval.
- **Network Isolation:** All outbound requests must pass through `connectors/unreal_bridge.py`.
- **Explainability:** Each proposal includes machine-generated rationale logged to the history database.

Refer to `docs/ARCHITECTURE.md` for a comprehensive overview of the subsystem interactions and workflows.
