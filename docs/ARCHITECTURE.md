# Architecture Overview

Grounded Lifestyle is organised as a civic metaphor:

- **Laws** define non-negotiable rules such as `laws/constitution.yaml` and `laws/economy_rules.yaml`.
- **Government** orchestrates ideation, storage, and presentation via the orchestrator, proposal manager, and presenter.
- **Entrepreneurs** create venture blueprints with specialised agents (venture, optimizer, marketer, writer).
- **Website** hosts the public portfolio for https://groundedlifestyle.org.
- **Interface** offers human tooling (CLI + dashboard) to approve and publish work.
- **Memory** stores analytics hints and run histories for iterative learning.

## Flow of a Venture
1. The venture agent gathers metrics from `memory/analytics.py` and proposes an idea.
2. `government/proposal_manager.py` serialises the proposal into `scriptSuggestions/<proposal>/proposal.yaml`.
3. Humans review the artefacts using `python -m interface.cli show <id>` or the Flask dashboard.
4. Upon approval, `government/presenter.py` renders updated HTML for the public site.
5. Deployment is manual via `website/deploy.py` to maintain explicit human oversight.

## Safety Features
- All proposals require `require_human_approval: true`.
- `laws/economy_rules.yaml` restricts budgets, domains, and automation scope.
- Agents operate in sandbox directories defined by `config/settings.yaml`.
- The CLI exposes only supervised commands: generate venture, list/show/approve proposals, publish site.

## Directory Highlights
```
Self-Coding-Bot/
├── government/
│   ├── presenter.py        # Builds static portfolio pages
│   └── proposal_manager.py # Loads & persists proposal manifests
├── entrepreneurs/
│   ├── venture_agent.py    # Produces new venture ideas
│   ├── optimizer_agent.py  # Technical recommendations
│   └── marketer_agent.py   # SEO & outreach playbooks
├── website/
│   ├── app.py              # Flask app for public portfolio
│   └── templates/          # base.html, home.html, venture_page.html
├── scriptSuggestions/      # Proposal folders awaiting review
├── interface/
│   ├── cli.py              # `brain` supervision commands
│   └── dashboard.py        # Local Flask review UI
└── docs/                   # Guides for operators
```

This modular structure ensures the motto “Propose, never presume” remains intact: every idea is surfaced with context, aesthetics, and ethical guardrails, while humans retain the final say.
