import asyncio
from octobot.core.events import EventBus
from octobot.core.proposals import ProposalManager
from octobot.core.orchestrator import Orchestrator

async def main():
    print("[OctoBot] Starting core systems...")

    event_bus = EventBus()
    proposals = ProposalManager()
    orchestrator = Orchestrator(event_bus, proposals)

    # Subscribe orchestrator to proposal lifecycle events
    event_bus.subscribe("proposal_approved", orchestrator.on_proposal_approved)
    event_bus.subscribe("proposal_rejected", orchestrator.on_proposal_rejected)

    # Launch the orchestrator loop
    await orchestrator.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
