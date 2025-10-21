"""Tests for the local LLM client stub mode."""
from reasoning.local_llm_client import LocalLLMClient


def test_stub_generation_is_deterministic() -> None:
    client = LocalLLMClient(use_stub=True)
    prompt = "Explain the architecture."
    first = client.generate(prompt)
    second = client.generate(prompt)
    assert first == second
    assert "Stub response" in first
