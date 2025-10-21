"""Deterministic embedding utilities for semantic recall."""
from __future__ import annotations

import hashlib
from typing import List


def embed_text(text: str, dimensions: int = 128) -> List[float]:
    """Create a deterministic pseudo-embedding for text."""

    if dimensions <= 0:
        raise ValueError("dimensions must be positive")
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = list(digest)
    while len(values) < dimensions:
        digest = hashlib.sha256(bytes(values)).digest()
        values.extend(digest)
    normalized = [value / 255.0 for value in values[:dimensions]]
    return normalized


def cosine_similarity(vector_a: List[float], vector_b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""

    if len(vector_a) != len(vector_b):
        raise ValueError("Vectors must be the same length")
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    magnitude_a = sum(value * value for value in vector_a) ** 0.5
    magnitude_b = sum(value * value for value in vector_b) ** 0.5
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    return dot_product / (magnitude_a * magnitude_b)
