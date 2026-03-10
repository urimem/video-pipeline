import json
import logging
import os
from typing import Callable, Awaitable

import httpx

from session.state import SessionState
from agent.tools import TOOLS
from agent.system_prompt import SYSTEM_PROMPT
from agent.tool_handlers import handle_tool_call

logger = logging.getLogger(__name__)

OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


WsSend = Callable[[dict], Awaitable[None]]


def _build_system(state: SessionState) -> str:
    """Inject current pipeline state into the system prompt each turn."""
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"## Current Pipeline State\n"
        f"- Current step: {state.pipeline_step}\n"
        f"- Script saved: {bool(state.script)}\n"
        f"- Images generated: {len(state.images)}\n"
        f"- Video ready: {bool(state.video_url)}\n"
    )


def _build_messages(state: SessionState) -> list[dict]:
    """Build the messages list with the dynamic system prompt."""
    return [
        {"role": "system", "content": _build_system(state)},
        *state.messages,
    ]


async def run_agent_turn(
    user_message: str,
    state: SessionState,
    ws_send: WsSend,
) -> None:
    """
    Run one full agent turn.

    May involve multiple API calls if the model uses tools (the agentic loop).
    Streams text tokens to the WebSocket as they arrive for a typewriter effect.
    """
    state.messages.append({"role": "user", "content": user_message})

    while True:
        messages = _build_messages(state)
        logger.info("Calling OpenAI API (messages=%d)", len(messages))

        payload = {
            "model": "gpt-5.1-chat-latest",
            "max_completion_tokens": 4096,
            "stream": True,
            "messages": messages,
            "tools": TOOLS,
        }
        text_content = ""
        tool_calls_by_index: dict[int, dict] = {}
        finish_reason = None
        chunk_count = 0

        logger.info(
            "Sending payload: model=%s, stream=%s, tools=%s, message_roles=%s",
            payload["model"],
            payload["stream"],
            [t["function"]["name"] for t in payload["tools"]],
            [m["role"] for m in payload["messages"]],
        )

        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as http:
            async with http.stream(
                "POST",
                f"{OPENAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            ) as resp:
                logger.info("OpenAI response: status=%d content_type=%s", resp.status_code, resp.headers.get("content-type", ""))

                # Read full body for non-SSE responses (error case)
                content_type = resp.headers.get("content-type", "")
                if "text/event-stream" not in content_type:
                    body = await resp.aread()
                    logger.error("OpenAI returned non-SSE response: %s", body.decode()[:1000])
                    raise RuntimeError(f"OpenAI API error: {body.decode()[:500]}")

                # Parse SSE stream
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        logger.warning("Unparseable SSE chunk: %s", data[:200])
                        continue

                    chunk_count += 1
                    logger.info("SSE chunk #%d: %s", chunk_count, data)
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    choice = choices[0]
                    delta = choice.get("delta", {})
                    finish_reason = choice.get("finish_reason") or finish_reason

                    # Stream text tokens to frontend
                    if delta.get("content"):
                        text_content += delta["content"]
                        await ws_send({
                            "type": "agent_token",
                            "data": {"token": delta["content"]},
                        })

                    # Accumulate tool call fragments
                    for tc_delta in delta.get("tool_calls", []):
                        idx = tc_delta["index"]
                        if idx not in tool_calls_by_index:
                            tool_calls_by_index[idx] = {
                                "id": tc_delta.get("id", ""),
                                "name": "",
                                "arguments": "",
                            }
                        entry = tool_calls_by_index[idx]
                        if tc_delta.get("id"):
                            entry["id"] = tc_delta["id"]
                        func = tc_delta.get("function", {})
                        if func.get("name"):
                            entry["name"] = func["name"]
                        if func.get("arguments"):
                            entry["arguments"] += func["arguments"]

        logger.info(
            "Stream complete: chunks=%d, text_len=%d, tool_calls=%d, finish=%s",
            chunk_count, len(text_content), len(tool_calls_by_index), finish_reason,
        )

        if chunk_count == 0:
            raise RuntimeError("kie.ai returned an empty SSE stream — no data chunks received.")

        # Build the assistant message for conversation history
        assistant_message: dict = {"role": "assistant", "content": text_content or None}
        if tool_calls_by_index:
            assistant_message["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"],
                    },
                }
                for tc in sorted(tool_calls_by_index.values(), key=lambda t: t["id"])
            ]
        state.messages.append(assistant_message)

        # No tool calls → model is done for this turn
        if not tool_calls_by_index:
            await ws_send({"type": "agent_turn_complete", "data": {}})
            return

        # Execute each tool call and collect results
        for tc in sorted(tool_calls_by_index.values(), key=lambda t: t["id"]):
            tool_name = tc["name"]
            tool_input = json.loads(tc["arguments"])

            await ws_send({
                "type": "tool_use",
                "data": {
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                },
            })

            result_text = await handle_tool_call(
                tool_name=tool_name,
                tool_input=tool_input,
                state=state,
                ws_send=ws_send,
            )

            # Feed tool result back (OpenAI protocol)
            state.messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result_text,
            })

        # Loop: model will respond to the tool results, possibly calling more tools
