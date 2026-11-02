"""
OpenAI-compatible chat completions endpoint with Browser Bridge support.
"""
import asyncio
import json
import logging
import time
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from config import Config
from core.sse_parser import (
    parse_sse_line,
    extract_assistant_text,
    compute_delta,
    openai_chunk,
    openai_completion,
)
from core.exceptions import RateLimitError, TokenExpiredError, NoAccountsError
from api.routes_bridge import pending_jobs, active_job_queues

log = logging.getLogger("api.chat")
router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "gpt-4o"
    messages: list[Message]
    stream: bool = True
    temperature: float | None = None


# Injected at app assembly
conversation_store = None
token_pool = None
cf_manager = None


def build_upstream_payload(request: ChatRequest, state: dict) -> dict:
    """Map OpenAI messages -> ChatGPT web payload."""
    system_msg = None
    user_messages = []
    for msg in request.messages:
        if msg.role == "system":
            system_msg = msg.content
        else:
            user_messages.append(msg)

    last_msg = user_messages[-1] if user_messages else None
    last_msg_content = last_msg.content if last_msg else (system_msg or "")

    msg_id = str(uuid.uuid4())
    now_ts = time.time()

    messages = [{
        "id": msg_id,
        "author": {"role": "user", "name": None, "metadata": {}},
        "channel": None,
        "content": {"content_type": "text", "parts": [last_msg_content]},
        "create_time": now_ts,
        "end_turn": None,
        "metadata": {
            "automation_creation_attribution": {
                "origin": "conversation",
                "flow_id": msg_id,
            }
        },
        "recipient": "all",
        "status": "finished_successfully",
        "update_time": None,
        "weight": 1,
    }]

    if system_msg:
        sys_id = str(uuid.uuid4())
        messages.insert(0, {
            "id": sys_id,
            "author": {"role": "system", "name": None, "metadata": {}},
            "channel": None,
            "content": {"content_type": "text", "parts": [system_msg]},
            "create_time": now_ts,
            "end_turn": None,
            "metadata": {"is_system_message": True},
            "recipient": "all",
            "status": "finished_successfully",
            "update_time": None,
            "weight": 1,
        })

    model_slug = request.model
    if model_slug in ["gpt-4o", "gpt-4", "gpt-3.5-turbo"]:
        model_slug = "auto"

    parent_id = state.get("parent_message_id") or str(uuid.uuid4())
    conv_id = state.get("conversation_id")

    payload = {
        "turn_attribution": {"turn_trigger": "composer"},
        "action": "next",
        "messages": messages,
        "parent_message_id": parent_id,
        "model": model_slug,
        "timezone": "Asia/Saigon",
        "timezone_offset_min": -420,
        "history_and_training_disabled": True,
        "client_contextual_info": {
            "app_name": "chatgpt.com",
            "app_surface": "codex_browser",
            "has_web_push_capabilities": True,
            "web_push_notification_permission": "default",
        },
        "local_function_names": ["local.continue_in_work"],
        "supported_encodings": ["v1"],
        "genui_state_snapshots": [],
        "client_prepare_state": "success",
    }

    if conv_id:
        payload["conversation_id"] = conv_id

    return payload


async def bridge_stream_generator(payload: dict, client_session: str, model: str):
    """Wait for Chrome tab bridge to execute payload and stream SSE chunks."""
    job_id = str(uuid.uuid4())
    job_queue = asyncio.Queue()
    active_job_queues[job_id] = job_queue

    auth_info = {}
    if token_pool:
        try:
            account = token_pool.get_account()
            if account:
                auth_info = {
                    "token": account.token,
                    "account_id": "83f209d0-1b7e-4f54-8d1e-24afbf7b6e94",
                }
        except Exception:
            pass

    # Put job for browser tab to claim
    await pending_jobs.put({
        "job_id": job_id,
        "payload": payload,
        "prompt_text": payload["messages"][-1]["content"]["parts"][0] if payload["messages"] else "",
        "model": model,
        "auth": auth_info,
    })

    # Yield first role announcement frame
    yield f"data: {openai_chunk(model)}\n\n"

    accumulated_text = ""
    conversation_id = None
    parent_message_id = None

    try:
        buffer = ""
        done_streaming = False
        while True:
            # 60s timeout per chunk
            item = await asyncio.wait_for(job_queue.get(), timeout=60.0)

            if item.get("done"):
                break

            if item.get("error"):
                log.error("Bridge reported error: %s", item["error"])
                yield f"data: {json.dumps({'error': {'message': item['error']}})}\n\n"
                break

            raw_chunk = item.get("chunk", "")
            buffer += raw_chunk

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.rstrip("\r")

                if line.strip() == "data: [DONE]":
                    done_streaming = True
                    break

                event = parse_sse_line(line)
                if event is None or not isinstance(event, dict):
                    continue

                if event.get("conversation_id"):
                    conversation_id = event["conversation_id"]

                text, message_id, is_delta = extract_assistant_text(event)
                if message_id:
                    parent_message_id = message_id
                if text is not None:
                    if is_delta:
                        delta = text
                        accumulated_text += text
                    else:
                        delta = compute_delta(accumulated_text, text)
                        accumulated_text = text
                    if delta:
                        yield f"data: {openai_chunk(model, delta_content=delta)}\n\n"

            if done_streaming:
                break

        if conversation_id:
            conversation_store.update(client_session, conversation_id, parent_message_id)

    except asyncio.TimeoutError:
        log.error("Timeout waiting for Chrome bridge to process job %s", job_id)
        yield f"data: {json.dumps({'error': {'message': 'Timeout waiting for Chrome tab bridge'}})}\n\n"
    finally:
        active_job_queues.pop(job_id, None)

    yield f"data: {openai_chunk(model, finish_reason='stop')}\n\n"
    yield "data: [DONE]\n\n"


@router.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest, req: Request):
    client_session = req.headers.get("x-session-id") or str(uuid.uuid4())

    state = conversation_store.get(client_session)
    payload = build_upstream_payload(request, state)

    if request.stream:
        return StreamingResponse(
            bridge_stream_generator(payload, client_session, request.model),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Non-streaming collection
    full_text = ""
    error_msg = None
    async for frame in bridge_stream_generator(payload, client_session, request.model):
        data_str = frame.removeprefix("data: ").strip()
        if data_str == "[DONE]":
            continue
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            continue
        if "error" in data:
            error_msg = data["error"].get("message", "unknown error")
            continue
        delta = data["choices"][0]["delta"].get("content")
        if delta:
            full_text += delta

    if error_msg and not full_text:
        return JSONResponse(
            {"error": {"message": error_msg, "type": "bridge_error"}},
            status_code=502,
        )

    return openai_completion(request.model, full_text)
