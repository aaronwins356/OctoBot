# Human Approval Checklist

Follow this checklist when supervising a venture proposal.

1. **Generate / Fetch**
   - Request ideas with `python -m interface.cli generate-venture` or inspect existing folders in `scriptSuggestions/`.
   - Read `proposal.yaml` to confirm the ethical statement and financial boundaries.

2. **Static Review**
   - Run `make lint` and `make test` when new code accompanies the proposal.
   - Inspect for disallowed imports or filesystem writes beyond allowed directories.

3. **Risk Assessment**
   - Compare the idea against `laws/economy_rules.yaml` and personal standards.
   - Confirm `require_human_approval` remains `true` and budgets stay within $50.

4. **Approval**
   - Approve with `python -m interface.cli approve <folder_name>` once satisfied.
   - Document any rationale or concerns in commit messages or reflections.

5. **Publication**
   - Rebuild the public portfolio via `python -m interface.cli publish-site`.
   - Manually deploy the generated files in `website/public/` to the hosting provider.

6. **Post-Approval Monitoring**
   - Update `memory/` entries or analytics once real-world results are observed.
   - Log reflections to maintain traceability of human decisions.

This workflow keeps humans firmly in control while enabling transparent collaboration with the venture agents.
