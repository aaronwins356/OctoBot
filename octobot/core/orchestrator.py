import asyncio
import structlog
from octobot.core.events import EventBus
from octobot.core.proposals import ProposalManager

log = structlog.get_logger()

async def orchestrate():
    bus = EventBus()
    proposals = ProposalManager()

    async def on_approved(proposal_id):
        log.info("orchestrator.applied", proposal_id=proposal_id)

    bus.subscribe("proposal_approved", on_approved)

    log.info("orchestrator.ready", count=len(proposals.proposals))
    while True:
        event, data = await bus.queue.get()
        log.info("orchestrator.event", event=event, data=data)

if __name__ == "__main__":
    asyncio.run(orchestrate())
