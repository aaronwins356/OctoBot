import asyncio

import pytest

from octobot.core.events import EventBus


@pytest.mark.anyio("asyncio")
async def test_event_bus_emits_and_notifies():
    bus = EventBus()
    received = asyncio.Event()
    payload = {}

    async def handler(proposal_id):
        payload["proposal_id"] = proposal_id
        received.set()

    bus.subscribe("proposal_approved", handler)
    await bus.emit("proposal_approved", proposal_id="123")

    await asyncio.wait_for(received.wait(), timeout=1)
    assert payload["proposal_id"] == "123"
    assert await bus.queue.get() == ("proposal_approved", {"proposal_id": "123"})
