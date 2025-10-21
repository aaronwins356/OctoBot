import asyncio
from structlog import get_logger

logger = get_logger()


class Orchestrator:
    """
    The Orchestrator is the central coordinator for OctoBot.
    It listens to proposal and event updates, and manages
    evaluation and execution cycles.
    """

    def __init__(self, event_bus, proposal_manager):
        self.event_bus = event_bus
        self.proposal_manager = proposal_manager
        self.running = False

    async def run_forever(self):
        """Run the main orchestration loop."""
        self.running = True
        logger.info("orchestrator.started")

        # Subscribe to proposal events
        self.event_bus.subscribe("proposal_created", self.on_proposal_created)
        self.event_bus.subscribe("proposal_approved", self.on_proposal_approved)
        self.event_bus.subscribe("proposal_rejected", self.on_proposal_rejected)

        while self.running:
            await asyncio.sleep(5)
            logger.info("orchestrator.heartbeat", status="alive")

    async def stop(self):
        """Gracefully stop orchestration."""
        self.running = False
        logger.info("orchestrator.stopped")

    # --- Event Handlers ---

    async def on_proposal_created(self, proposal):
        logger.info("proposal.created", proposal=proposal)
        await self.proposal_manager.evaluate(proposal)

    async def on_proposal_approved(self, proposal):
        logger.info("proposal.approved", proposal=proposal)

    async def on_proposal_rejected(self, proposal):
        logger.info("proposal.rejected", proposal=proposal)
