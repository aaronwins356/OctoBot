# Safety Policy

OctoBot operates under a constitution defined in `laws/constitution.yaml`. The core principles are enforced by the `laws.validator.enforce` function.

- **External Requests** — Only `connectors/unreal_bridge.py` may initiate external interactions. All other modules must remain offline.
- **Filesystem Writes** — Agents may only write to directories inside `/proposals` or `/ventures`. Reports and temporary files are stored under `proposals/_workspace/` to comply.
- **Code Merge** — Applying patches requires an explicit human approval flag. The updater refuses to run otherwise.

Whenever a rule is checked, a JSON entry is appended to `memory/audit.log` and a structured event is emitted to `memory/system.log`. Violations raise `RuleViolationError` and halt execution immediately.

Operators are encouraged to review the audit log regularly and confirm that every approval is intentional.
