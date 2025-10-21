# OctoBot Hardened Architecture

<!--
File: README.md
Fix Type: Documentation
Summary:
- ✅ Fixed: outdated documentation missing security controls
- ✅ Added: explanation of shared auth and safe filesystem pipeline
- ✅ Tested by: docs linting via tests/test_docs.py
-->

OctoBot is a constitutional automation framework that now enforces secure,
human-governed proposal lifecycles. This README summarises the hardened
components introduced in the refactor proposal.

## Architecture Overview

```text
┌─────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  Interface  │────▶ │ Shared Auth Gate │────▶ │ Orchestrator    │
│  (CLI/UI)   │      │ (OCTOBOT_KEY)    │      │ & Event Bus     │
└────┬────────┘      └────────┬─────────┘      └────────┬────────┘
     │                         │                        │
     │                         │                        ▼
     │                         │                ┌─────────────────┐
     │                         │                │ Validator & Laws │
     │                         │                │ (Coverage ≥ 0.9) │
     │                         │                └────────┬────────┘
     │                         │                        │
     ▼                         ▼                        ▼
┌─────────────┐       ┌─────────────────┐       ┌────────────────────┐
│ Analyzer    │       │ Persistence API │       │ Update & Ledger     │
│ (Resilient) │       │ (safe_write)    │       │ (Audited Commits)   │
└─────────────┘       └─────────────────┘       └────────────────────┘
```

Key flows:

1. **Authentication** – every dashboard and Chat Unreal route invokes the shared
   `octobot.security.auth_shared` module. Startup aborts if `OCTOBOT_KEY` is
   missing, enforcing a fail-closed posture.
2. **Proposal Lifecycle** – `Orchestrator` now validates proposals before
   approval, ensuring coverage fractions stay ≥ 0.90 and validator compliance is
   confirmed.
3. **Filesystem Safety** – `octobot.utils.persistence.safe_write` routes all
   writes through the constitutional enforcer, capturing audit logs for every
   mutation.

## Shared Authentication

- `octobot/security/auth_shared.py` centralises token verification.
- Flask (`chat_unreal`) and FastAPI (dashboard) import the same helpers to
  guarantee uniform human approval checks.
- Missing or incorrect tokens return HTTP 401/403 instead of allowing partial
  execution.

## Validator Resilience

- `octobot/laws/validator.validate_json` prevents malformed artefacts from
  crashing validation runs.
- Coverage values are normalised to fractions; the UI only scales to percentages
  for display.
- Failed validations append detailed issues to the `ValidationReport`.

## Orchestrator Hardening

- Each `Orchestrator` instance hosts its own `EventBus`, making tests and
  concurrent orchestrators deterministic.
- Approval now triggers test execution only after the validation pass confirms
  compliance.
- Ledger entries record creation, validation, and approval stages for audit
  transparency.

## Analyzer & Connectors

- The analyzer agent skips `.git`, `.venv`, `node_modules`, and `__pycache__`
  paths, logging any Unicode or syntax issues while continuing the scan.
- Connectors validate every outbound URL through the new domain validator to
  prevent hostname spoofing (`api.github.com` is the sole GitHub endpoint).

## Continuous Integration

- GitHub Actions workflow installs dependencies via Poetry and runs pytest with
  coverage thresholds ≥ 90%.
- Development dependencies such as pytest, coverage, and flake8 live in the
  `dev` dependency group of `pyproject.toml`.

## Law Transparency

- The `docs/CONSTITUTION.md` (to be generated) summarises the guiding laws of
  OctoBot for human reviewers.
- Ledger and audit logs are updated whenever `safe_write` is invoked, providing
  a trace of all filesystem actions.

## Verification Plan

Recommended command suite:

```bash
poetry install --with dev
poetry run pytest --maxfail=1 --disable-warnings -q
poetry run coverage report --fail-under=90
```

Each section above is paired with dedicated unit tests under `tests/` to confirm
behaviour for missing tokens, malformed JSON, invalid domains, and orchestrator
approval guards.

