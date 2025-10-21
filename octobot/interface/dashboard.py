from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path

# Safe import: allows local development even if auth_shared doesn't exist
try:
    from octobot.security.auth_shared import verify_token
except ImportError:
    def verify_token():
        # Dummy dev-mode token verifier
        async def _dummy():
            return "dev-mode"
        return _dummy

from octobot.core.proposals import ProposalManager
from octobot.core.events import EventBus

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def create_app() -> FastAPI:
    app = FastAPI(
        title="OctoBot Governance Dashboard",
        description="Human-facing dashboard for proposal validation and approval.",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.proposal_manager = ProposalManager()
    app.state.event_bus = EventBus()

    # ---------------- ROUTES ----------------

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        proposals = app.state.proposal_manager.list_all()
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "proposals": proposals},
        )

    @app.get("/proposal/{proposal_id}", response_class=HTMLResponse)
    async def view_proposal(request: Request, proposal_id: str):
        proposal = app.state.proposal_manager.get(proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        return templates.TemplateResponse(
            "proposal.html",
            {"request": request, "proposal": proposal},
        )

    @app.post("/approve/{proposal_id}")
    async def approve_proposal(proposal_id: str, token: str = Depends(verify_token)):
        pm = app.state.proposal_manager
        ev = app.state.event_bus
        proposal = pm.get(proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")

        coverage = float(proposal.metadata.get("coverage", 0))
        if coverage < 0.9:
            raise HTTPException(status_code=400, detail="Coverage below 90%")

        pm.mark_approved(proposal_id, approver="dashboard", token=token)
        await ev.emit("proposal_approved", proposal_id=proposal_id)
        return JSONResponse({"status": "approved", "proposal_id": proposal_id})

    @app.post("/reject/{proposal_id}")
    async def reject_proposal(proposal_id: str, token: str = Depends(verify_token)):
        pm = app.state.proposal_manager
        ev = app.state.event_bus
        if not pm.exists(proposal_id):
            raise HTTPException(status_code=404, detail="Proposal not found")

        pm.mark_rejected(proposal_id, reason="Manual rejection from dashboard")
        await ev.emit("proposal_rejected", proposal_id=proposal_id)
        return JSONResponse({"status": "rejected", "proposal_id": proposal_id})

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    return app


app = create_app()

__all__ = ["app", "create_app"]


