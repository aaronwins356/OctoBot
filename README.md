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
government/           # Orchestration, proposal management, scoring, merging
engineers/            # Specialized agents for analysis, code drafting, testing, and documentation
laws/                 # Constitutional documents and validator enforcing compliance
connectors/           # Interfaces to external systems (stubbed for offline demonstration)
interface/            # Human-facing CLI and Flask dashboard
memory/               # SQLite persistence, metrics, and logging utilities
proposals/            # Generated proposal packages awaiting review
scripts/              # Helper scripts for bootstrapping and maintenance
docs/                 # Architectural documentation and user guides
tests/                # Automated regression tests
```

## Getting Started
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Initialize the database and generate example proposals:
   ```bash
   python -m interface.cli analyze
   python -m interface.cli propose
   ```
3. Launch the dashboard to inspect proposals, laws, and history:
   ```bash
   python -m interface.cli serve
   ```
4. Approve a proposal through the dashboard or CLI, then apply it with the updater.

## Safety Principles
- **No Unreviewed Execution:** `laws/constitution.yaml` forbids automatic merges without human approval.
- **Network Isolation:** All outbound requests must pass through `connectors/unreal_bridge.py`.
- **Explainability:** Each proposal includes machine-generated rationale logged to the history database.

Refer to `docs/ARCHITECTURE.md` for a comprehensive overview of the subsystem interactions and workflows.
