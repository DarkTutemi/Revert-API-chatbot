import json
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from core.sse_parser import openai_chunk, openai_completion
from providers.base import UpstreamError, ChatMessage

log = logging.getLogger("api.chat")
router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[Message]
    stream: bool = True
    temperature: float | None = None


provider_instance = None  # injected at app assembly


@router.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    model = request.model or "deepseek-reasoner"
    messages = [ChatMessage(role=m.role, content=m.content) for m in request.messages if m.content]
    if not messages:
        return JSONResponse(
            {"error": {"message": "no messages", "type": "invalid_request"}},
            status_code=400,
        )

    if request.stream:
        return StreamingResponse(
            stream_gen(messages, model, request.temperature),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    try:
        text = await provider_instance.chat(messages, model, request.temperature)
    except UpstreamError as e:
        return JSONResponse(
            {"error": {"message": e.message, "type": "upstream_error",
                       "provider": e.provider}},
            status_code=502,
        )
    return openai_completion(model, text)


async def stream_gen(messages, model, temperature):
    yield f"data: {openai_chunk(model)}\n\n"
    try:
        async for delta in provider_instance.stream_chat(messages, model, temperature):
            yield f"data: {openai_chunk(model, delta_content=delta)}\n\n"
        yield f"data: {openai_chunk(model, finish_reason='stop')}\n\n"
    except UpstreamError as e:
        yield f"data: {json.dumps({'error': {'message': e.message, 'provider': e.provider}})}\n\n"
    yield "data: [DONE]\n\n"
