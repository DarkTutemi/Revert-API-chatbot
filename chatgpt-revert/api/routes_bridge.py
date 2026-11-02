"""
Browser Bridge routes: coordinates between client /v1/chat/completions
and paneer's real authenticated ChatGPT Chrome tab.
"""
import asyncio
import json
import logging
from typing import Dict
from fastapi import APIRouter
from pydantic import BaseModel

log = logging.getLogger("api.bridge")
router = APIRouter(prefix="/bridge")

# Queue of jobs waiting for the browser to pick up
pending_jobs: asyncio.Queue = asyncio.Queue()

# Dict of active job queues (where chunks are pushed to waiting stream clients)
active_job_queues: Dict[str, asyncio.Queue] = {}


class ChunkPayload(BaseModel):
    job_id: str
    chunk: str


class DonePayload(BaseModel):
    job_id: str


class ErrorPayload(BaseModel):
    job_id: str
    error: str


@router.get("/poll")
async def poll_job():
    """Browser tab calls this to receive the next chat request."""
    try:
        # Wait up to 25s for a job (long-polling)
        job = await asyncio.wait_for(pending_jobs.get(), timeout=25.0)
        log.info("Handed job %s to browser bridge", job.get("job_id"))
        return job
    except asyncio.TimeoutError:
        return {"job_id": None}


@router.get("/poll_now")
async def poll_now():
    """Non-blocking instant poll for extension content script."""
    try:
        job = pending_jobs.get_nowait()
        log.info("Handed job %s to browser bridge via poll_now", job.get("job_id"))
        return job
    except asyncio.QueueEmpty:
        return {"job_id": None}


@router.post("/chunk")
async def receive_chunk(data: ChunkPayload):
    """Browser tab posts raw SSE chunks here."""
    log.info("Received chunk for job %s (len=%d): %r", data.job_id, len(data.chunk), data.chunk[:100])
    q = active_job_queues.get(data.job_id)
    if q:
        await q.put({"chunk": data.chunk})
    return {"status": "ok"}


@router.post("/done")
async def receive_done(data: DonePayload):
    """Browser tab signals stream completion."""
    log.info("Received done for job %s", data.job_id)
    q = active_job_queues.get(data.job_id)
    if q:
        await q.put({"done": True})
    return {"status": "ok"}


@router.post("/error")
async def receive_error(data: ErrorPayload):
    """Browser tab signals error."""
    q = active_job_queues.get(data.job_id)
    if q:
        await q.put({"error": data.error})
    return {"status": "ok"}


@router.get("/status")
async def bridge_status():
    """Check how many clients or jobs are connected."""
    return {
        "pending_jobs": pending_jobs.qsize(),
        "active_jobs": len(active_job_queues),
    }
