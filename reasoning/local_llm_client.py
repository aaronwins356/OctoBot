"""Local language model client with optional transformer backend."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Generator


def _default_model_dir() -> str:
    return os.environ.get("MODEL_DIR", "/workspace/models")


@dataclass
class LocalLLMClient:
    """Wrap a local LLM or deterministic stub for testing."""

    model_id: str = "sshleifer/tiny-gpt2"
    max_new_tokens: int = 128
    use_stub: bool = False

    def __post_init__(self) -> None:
        self._backend = "stub"
        self._tokenizer = None
        self._model = None
        if not self.use_stub:
            self._load_transformer_model()

    def _load_transformer_model(self) -> None:
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch

            model_dir = _default_model_dir()
            os.makedirs(model_dir, exist_ok=True)
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                cache_dir=model_dir,
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                cache_dir=model_dir,
            )
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model.to(device)
            self._device = device
            self._backend = "transformers"
        except Exception:
            self._backend = "stub"

    def generate(self, prompt: str) -> str:
        """Generate a completion for the provided prompt."""

        if self._backend == "transformers" and self._tokenizer and self._model:
            return self._generate_with_transformer(prompt)
        return self._generate_with_stub(prompt)

    def stream_generate(self, prompt: str) -> Generator[str, None, None]:
        """Yield tokens incrementally for streaming responses."""

        if self._backend == "transformers" and self._tokenizer and self._model:
            yield from self._stream_with_transformer(prompt)
        else:
            yield self._generate_with_stub(prompt)

    def _generate_with_transformer(self, prompt: str) -> str:
        import torch

        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._device)
        output_tokens = self._model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
        )
        text = self._tokenizer.decode(output_tokens[0], skip_special_tokens=True)
        return text

    def _stream_with_transformer(self, prompt: str) -> Generator[str, None, None]:
        from transformers import TextIteratorStreamer
        import torch

        streamer = TextIteratorStreamer(self._tokenizer, skip_prompt=True, skip_special_tokens=True)
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._device)
        generation_kwargs = dict(
            **inputs,
            streamer=streamer,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
        )
        self._model.generate(**generation_kwargs)
        for text in streamer:
            yield text

    @staticmethod
    def _generate_with_stub(prompt: str) -> str:
        """Return a deterministic stubbed response when models are unavailable."""

        fingerprint = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
        return (
            f"Stub response for: {prompt}\n"
            f"Fingerprint: {fingerprint}\n"
            "This output is deterministic and suitable for testing."
        )
