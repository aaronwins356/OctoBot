# Grounded Lifestyle Venture Guide

Grounded Lifestyle operates as a human-supervised AI venture studio. This guide describes the lifecycle of a venture from ideation to publication.

## 1. Idea Generation
- Run `python -m interface.cli generate-venture` to request the venture agent to draft a proposal.
- The agent uses placeholder analytics and helper specialists (optimizer & marketer) to design a business concept.
- A new folder appears in `scriptSuggestions/` containing `proposal.yaml` and any supporting drafts.

## 2. Review & Ethics
- Read the generated `proposal.yaml` to ensure the idea aligns with `laws/economy_rules.yaml` and personal standards.
- The proposal must include an `ethical_statement` and may remain in `draft` status until human approval.

## 3. Approval Workflow
1. Inspect all artefacts locally.
2. Approve via CLI: `python -m interface.cli approve <folder_name>`.
3. Approved proposals gain a timestamp in `proposal.yaml` and become eligible for portfolio publication.

## 4. Portfolio Publication
- After approving at least one venture, run `python -m interface.cli publish-site`.
- The presenter renders HTML files into `website/public/` for manual deployment (Hostinger/Netlify recommended).

## 5. Continuous Learning
- The `memory/analytics.py` module can be replaced with real analytics pipelines once whitelisted.
- Always log reflections in `memory/` after major experiments to inform future ideation cycles.

## Safety Principles
- No code is deployed or executed automatically.
- All monetisation steps require explicit approval.
- Proposals avoid domains listed in `laws/economy_rules.yaml`.

For a deeper architectural overview read `docs/ARCHITECTURE.md`.
