"""
Browser Bridge routes for DeepSeek Web (chat.deepseek.com).
"""
import asyncio
import logging
import time
from typing import Dict
from fastapi import APIRouter
from pydantic import BaseModel

log = logging.getLogger("api.bridge")
router = APIRouter(prefix="/bridge")

pending_jobs: asyncio.Queue = asyncio.Queue()
active_job_queues: Dict[str, asyncio.Queue] = {}


class ChunkPayload(BaseModel):
    job_id: str
    chunk: str


class DonePayload(BaseModel):
    job_id: str


class LogPayload(BaseModel):
    message: str


class ErrorPayload(BaseModel):
    job_id: str
    error: str


@router.post("/log")
async def receive_log(data: LogPayload):
    log.info("[DEEPSEEK LOG] %s", data.message)
    return {"status": "ok"}


@router.get("/poll_now")
async def poll_now():
    """Non-blocking instant poll for DeepSeek extension content script."""
    while not pending_jobs.empty():
        job = pending_jobs.get_nowait()
        created_at = job.get("created_at", time.time())
        if time.time() - created_at > 90:
            log.warning("Discarded stale job %s (age=%.1fs)", job.get("job_id"), time.time() - created_at)
            continue
        log.info("Handed job %s to DeepSeek browser bridge (model=%s)", job.get("job_id"), job.get("model"))
        return job
    return {"job_id": None}


@router.post("/reset")
async def reset_bridge():
    """Clear all pending and active jobs."""
    cleared = 0
    while not pending_jobs.empty():
        pending_jobs.get_nowait()
        cleared += 1
    active_job_queues.clear()
    log.info("Reset bridge: cleared %d pending jobs and active queues", cleared)
    return {"status": "ok", "cleared": cleared}


@router.post("/chunk")
async def receive_chunk(data: ChunkPayload):
    log.info("Received chunk for job %s (len=%d): %r", data.job_id, len(data.chunk), data.chunk[:100])
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
        "pending_jobs": pending_jobs.qsize(),
        "active_jobs": len(active_job_queues),
    }
