# Architecture Overview

AI Republic models governance using a three-branch metaphor:

- **Laws** define immutable constraints. The constitution, validator, and audit utilities live here.
- **Government** orchestrates discovery, execution, auditing, and economic accounting for agents.
- **Entrepreneurs** implement BaseAgent subclasses that operate inside sandboxes and produce outputs or proposals.

The execution flow:

1. The orchestrator loads configuration and the constitution.
2. Agents are discovered in `entrepreneurs/` and statically validated before import.
3. In live mode, each agent is executed through a subprocess worker with an isolated sandbox directory.
4. Outputs and reports feed into memory storage, ledger accounting, and the audit log.
5. If an agent proposes code, the government packages the proposal, runs static checks, and drafts a PR (offline by default).
6. Human reviewers use the CLI to inspect, test, and manually merge proposals.

Supporting systems:

- **Memory** persists run data and allows summarisation and reflections without external services.
- **Economy** awards simulated credits tied to audit events, enabling transparent accounting.
- **Interface** (CLI) ensures human approval for code changes.

This architecture ensures safety by requiring static verification, sandboxed execution, and human gatekeeping for any system modifications.
