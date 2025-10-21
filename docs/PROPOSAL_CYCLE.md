# Proposal Cycle

The proposal pipeline is a deterministic finite-state machine managed by `government.orchestrator.Orchestrator`.

1. **Analyze** — Collect repository metrics (`engineers.analyzer_agent.AnalyzerAgent`).
2. **Propose** — Write proposal bundles to `proposals/YYYY-MM-DD_<topic>/` (`government.proposal_manager.ProposalManager`).
3. **Evaluate** — Enforce minimum test coverage (90%+) before marking a proposal ready.
4. **Present** — Surface proposals to humans via CLI and dashboard while waiting for approval.
5. **Await Approval** — Manual reviewers inspect `rationale.md`, `diff.patch`, and `impact.json`.
6. **Apply** — After approval, `government.updater.Updater` applies the patch, commits, and tags the repository (`vYYYY.MM.DD_<topic>`).

All transitions are logged with timestamps and Git SHAs. Proposal metadata is synchronised with `memory/memory.db` and mirrored in `proposal.yaml`.
