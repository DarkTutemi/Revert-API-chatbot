"""
Multi-Provider Browser Bridge routes for Unified AI Gateway (Port 3000).
Supports ChatGPT, Gemini, and DeepSeek via a single local server and all-in-one extension.
"""
import asyncio
import logging
import time
from typing import Dict, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

log = logging.getLogger("api.bridge")
router = APIRouter(prefix="/bridge")

# Dedicated pending queues for each provider
pending_jobs: Dict[str, asyncio.Queue] = {
    "chatgpt": asyncio.Queue(),
    "gemini": asyncio.Queue(),
    "deepseek": asyncio.Queue()
}

active_job_queues: Dict[str, asyncio.Queue] = {}


class ChunkPayload(BaseModel):
    job_id: str
    chunk: str


class DonePayload(BaseModel):
    job_id: str


class LogPayload(BaseModel):
    message: str
    provider: Optional[str] = "unknown"


class ErrorPayload(BaseModel):
    job_id: str
    error: str


@router.post("/log")
async def receive_log(data: LogPayload):
    log.info("[%s BRIDGE] %s", (data.provider or "WEB").upper(), data.message)
    return {"status": "ok"}


@router.get("/poll_now")
async def poll_now(provider: Optional[str] = Query(None)):
    """
    Non-blocking poll for browser extension.
    Returns next job matching requested provider (chatgpt, gemini, or deepseek).
    """
    target_providers = [provider.lower()] if provider and provider.lower() in pending_jobs else list(pending_jobs.keys())

    for p in target_providers:
        q = pending_jobs[p]
        while not q.empty():
            job = q.get_nowait()
            created_at = job.get("created_at", time.time())
            if time.time() - created_at > 90:
                log.warning("Discarded stale job %s for %s (age=%.1fs)", job.get("job_id"), p, time.time() - created_at)
                continue
            log.info("Handed job %s to %s browser bridge (model=%s)", job.get("job_id"), p, job.get("model"))
            return job

    return {"job_id": None}


@router.post("/reset")
async def reset_bridge():
    """Clear all pending and active jobs across all providers."""
    cleared = 0
    for p, q in pending_jobs.items():
        while not q.empty():
            q.get_nowait()
            cleared += 1
    active_job_queues.clear()
    log.info("Reset bridge: cleared %d pending jobs and active queues", cleared)
    return {"status": "ok", "cleared": cleared}


@router.post("/chunk")
async def receive_chunk(data: ChunkPayload):
    log.info("Received chunk for job %s (len=%d): %r", data.job_id, len(data.chunk), data.chunk[:80])
    q = active_job_queues.get(data.job_id)
    if q:
        await q.put({"chunk": data.chunk})
    return {"status": "ok"}


@router.post("/done")
async def receive_done(data: DonePayload):
    log.info("Received done for job %s", data.job_id)
    q = active_job_queues.get(data.job_id)
    if q:
        await q.put({"done": True})
    return {"status": "ok"}


@router.post("/error")
async def receive_error(data: ErrorPayload):
    log.error("Received error for job %s: %s", data.job_id, data.error)
    q = active_job_queues.get(data.job_id)
    if q:
        await q.put({"error": data.error})
    return {"status": "ok"}


@router.get("/status")
async def bridge_status():
    return {
        "pending_jobs": {p: q.qsize() for p, q in pending_jobs.items()},
        "active_jobs": len(active_job_queues),
    }
