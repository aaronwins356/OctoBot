# Grounded Lifestyle Venture Studio

Grounded Lifestyle is a human-supervised AI venture studio focused on ethically generating, evaluating, and presenting digital business ideas. The motto is **“Propose, never presume.”** Every artefact is drafted locally and requires explicit human approval before execution or deployment.

## Table of Contents
- [System Purpose](#system-purpose)
- [Architecture Overview](#architecture-overview)
- [Safety Principles](#safety-principles)
- [Quick Start](#quick-start)
- [Supervision Commands](#supervision-commands)
- [Deployment Guide](#deployment-guide)
- [Documentation](#documentation)

## System Purpose
The studio explores revenue opportunities such as wellness content sites, affiliate programs, and automation tools while respecting strict ethical and budgetary boundaries. Ideas are expressed as YAML proposals accompanied by explanatory text and optional code drafts.

## Architecture Overview
- `government/` — Orchestrator, proposal manager, presenter, and supporting utilities.
- `entrepreneurs/` — Specialised business agents (venture ideation, optimisation, marketing support).
- `laws/` — Constitutional rules and `economy_rules.yaml` describing financial constraints.
- `website/` — Flask application and templates for https://groundedlifestyle.org.
- `scriptSuggestions/` — Venture proposals awaiting human review.
- `interface/` — CLI (`python -m interface.cli`) and optional dashboard for approvals.
- `memory/` — Analytics scaffolding to guide future proposals.

See `docs/ARCHITECTURE.md` for a detailed walkthrough.

## Safety Principles
1. **Explicit Approval:** `laws/economy_rules.yaml` enforces `require_human_approval: true` on all proposals.
2. **Budget Guardrails:** Ventures must operate within a $50 budget ceiling and avoid disallowed domains (gambling, NSFW, political).
3. **No Auto-Deployment:** Static sites are built locally via `government/presenter.py` and must be uploaded manually.
4. **Sandboxed Agents:** Each agent runs in a dedicated sandbox and is statically validated before execution.
5. **Transparent Outputs:** Every proposal includes an ethical statement, projected costs, and expected revenue range.

## Quick Start
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Optional: copy `.env.example` to `.env` and set `OFFLINE_MODE=true` for fully local operation.

## Supervision Commands
Use the CLI to guide the venture lifecycle:
```bash
python -m interface.cli generate-venture   # Draft a new proposal
python -m interface.cli list-proposals     # View proposal directories
python -m interface.cli show <id>          # Display proposal.yaml
python -m interface.cli approve <id>       # Mark proposal as approved
python -m interface.cli publish-site       # Render updated portfolio HTML
```

A lightweight review dashboard is also available via `python -m interface.dashboard` (Flask app running on localhost).

## Deployment Guide
1. Approve at least one proposal.
2. Run `python -m interface.cli publish-site` to render HTML into `website/public/`.
3. Upload the generated assets to Hostinger, Netlify, or another hosting provider.
4. Update DNS for `groundedlifestyle.org` if necessary.

Deployment helpers in `website/deploy.py` intentionally stop short of pushing files to keep humans in control.

## Documentation
- `docs/VENTURE_GUIDE.md` — Detailed venture lifecycle instructions.
- `docs/ARCHITECTURE.md` — Expanded architectural overview.
- `docs/HUMAN_APPROVAL.md` — Human approval checklist.

For further experiments, edit `memory/analytics.py` with real metrics or extend the entrepreneur agents with new revenue hypotheses.
