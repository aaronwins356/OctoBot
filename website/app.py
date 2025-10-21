"""Flask application serving the Grounded Lifestyle public portfolio."""
from __future__ import annotations

from typing import List

from flask import Flask, abort, render_template

from government.proposal_manager import VentureProposal, filter_approved, load_proposals


def _load_portfolio() -> List[VentureProposal]:
    proposals = filter_approved(load_proposals())
    if not proposals:
        placeholder = VentureProposal(
            proposal_id="demo",
            proposal_name="Grounded Affiliate Blog",
            author_agent="venture_agent",
            description="A mindful wellness publication prototype awaiting human approval.",
            expected_cost="$0-$25 for hosting",
            expected_revenue="$50-150/month after 3 months",
            strategy="Draft SEO-informed articles and test affiliate integrations ethically.",
            ethical_statement="All published content will include transparent disclosures and promote wellbeing.",
            files_created=["website/templates/home.html"],
            status="preview",
            require_human_approval=True,
        )
        return [placeholder]
    return proposals


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    @app.context_processor
    def inject_globals() -> dict:
        return {"site_name": "Grounded Lifestyle"}

    @app.route("/")
    def home() -> str:
        ventures = _load_portfolio()
        approved = [venture for venture in ventures if venture.status.lower() == "approved"]
        # display placeholder if none approved
        display = approved if approved else ventures
        placeholder_mode = not approved
        return render_template("home.html", ventures=display, placeholder_mode=placeholder_mode)

    @app.route("/ventures/<proposal_id>")
    def venture_detail(proposal_id: str) -> str:
        ventures = _load_portfolio()
        for venture in ventures:
            if venture.slug == proposal_id:
                return render_template("venture_page.html", venture=venture)
        abort(404)

    @app.route("/about")
    def about() -> str:
        return render_template(
            "venture_page.html",
            venture=VentureProposal(
                proposal_id="about",
                proposal_name="Human-Supervised AI Entrepreneurship",
                author_agent="presenter",
                description=(
                    "Grounded Lifestyle pairs AI ideation with human judgment to explore"
                    " ethical digital ventures without unsupervised automation."
                ),
                expected_cost="Variable",
                expected_revenue="Long-term goodwill",
                strategy=(
                    "Propose, iterate, and refine ideas collaboratively with Aaron before any"
                    " execution or deployment steps."
                ),
                ethical_statement=(
                    "Every decision is reviewed by a human, ensuring transparent, responsible progress."
                ),
                files_created=[],
                status="reference",
                require_human_approval=True,
            ),
        )

    @app.route("/contact")
    def contact() -> str:
        return render_template(
            "venture_page.html",
            venture=VentureProposal(
                proposal_id="contact",
                proposal_name="Collaborate with Grounded Lifestyle",
                author_agent="presenter",
                description="We welcome thoughtful conversations about ethical, human-guided ventures.",
                expected_cost="N/A",
                expected_revenue="Relationship building",
                strategy="Email hello@groundedlifestyle.org to discuss opportunities.",
                ethical_statement="No unsolicited outreach; all conversations start with mutual consent.",
                files_created=[],
                status="reference",
                require_human_approval=True,
            ),
        )

    return app


app = create_app()
