"""FastAPI server exposing The Brain orchestrator and model endpoints."""
from __future__ import annotations

import json
import os
from pathlib import Path
from dataclasses import asdict
from typing import AsyncGenerator, Dict, Iterable, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from orchestrator.main_controller import ExecutiveOrchestrator, OrchestratorConfig
from reasoning.local_llm_client import LocalLLMClient
from memory.recall import MemoryRecall
from reasoning.reflection_engine import ReflectionEngine
from safety.audit_log import AuditLogger
from safety.rules import SafetyRules
from memory.embeddings import embed_text


app = FastAPI(title="The Brain")


def _load_settings() -> Dict[str, object]:
    settings_path = Path("config/settings.yaml")
    if not settings_path.exists():
        return {}
    try:
        import yaml

        with settings_path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except Exception:
        return {}


def _load_model_manifest() -> List[Dict[str, object]]:
    manifest_path = Path("config/model_manifest.json")
    if not manifest_path.exists():
        return []
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8")).get("models", [])
    except json.JSONDecodeError as exc:
        raise RuntimeError("Invalid model manifest") from exc


settings = _load_settings()
manifest_models = _load_model_manifest()
use_stub = os.environ.get("BRAIN_USE_STUB", "true").lower() in {"1", "true", "yes"}

orchestrator = ExecutiveOrchestrator(
    config=OrchestratorConfig(
        evaluation_threshold=float(
            settings.get("orchestrator", {}).get("evaluation_threshold", 0.6)
        ),
        max_depth=int(settings.get("orchestrator", {}).get("max_depth", 3)),
    ),
    llm_client=LocalLLMClient(use_stub=use_stub),
    memory=MemoryRecall(
        database_path=str(settings.get("memory", {}).get("database_path", "data/brain.db")),
        embedding_dim=int(settings.get("memory", {}).get("embedding_dim", 128)),
    ),
    reflection=ReflectionEngine(),
    audit_logger=AuditLogger(),
    safety_rules=SafetyRules(),
)


class GenerateRequest(BaseModel):
    """Input payload for text generation."""

    prompt: str
    stream: bool = False


class GenerateResponse(BaseModel):
    """Response payload for text generation."""

    response: str


class EmbedRequest(BaseModel):
    """Input payload for embeddings."""

    text: str
    dimensions: int | None = None


class EmbedResponse(BaseModel):
    """Response payload containing deterministic embeddings."""

    embedding: List[float]


@app.get("/health")
def health() -> Dict[str, str]:
    """Health check endpoint."""

    return {"status": "ok"}


@app.get("/models")
def list_models() -> Dict[str, List[Dict[str, object]]]:
    """Return the models declared in the manifest."""

    return {"models": manifest_models}


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest) -> JSONResponse | StreamingResponse:
    """Generate text using the local LLM client."""

    if request.stream:
        generator = orchestrator.llm_client.stream_generate(request.prompt)

        async def stream_wrapper() -> AsyncGenerator[str, None]:
            for chunk in generator:
                yield chunk

        return StreamingResponse(stream_wrapper(), media_type="text/plain")
    response_text = orchestrator.llm_client.generate(request.prompt)
    if not orchestrator.safety_rules.check_response(response_text):
        raise HTTPException(status_code=400, detail="Generated response violated safety rules")
    return JSONResponse(content=GenerateResponse(response=response_text).dict())


@app.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest) -> EmbedResponse:
    """Return a deterministic embedding for the text."""

    dimensions = request.dimensions or int(settings.get("memory", {}).get("embedding_dim", 128))
    embedding = embed_text(request.text, dimensions)
    return EmbedResponse(embedding=embedding)


@app.post("/goals/execute")
async def execute_goal(goal: str) -> Dict[str, object]:
    """Execute a goal using the orchestrator."""

    result = orchestrator.execute_goal(goal)
    return {
        "plan": result["plan"].to_dict(),
        "results": [asdict(evaluation) for evaluation in result["results"]],
        "insights": result["insights"],
    }
