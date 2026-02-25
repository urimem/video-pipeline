import json
import os
from typing import Callable, Awaitable

from openai import AsyncOpenAI

from session.state import SessionState
from agent.tools import TOOLS
from agent.system_prompt import SYSTEM_PROMPT
from agent.tool_handlers import handle_tool_call

client = AsyncOpenAI(
    api_key=os.getenv("KIE_API_KEY"),
    base_url="https://api.kie.ai/gemini-2.5-flash/v1",
)

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
        {"role": "developer", "content": _build_system(state)},
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
        # Stream the response
        stream = await client.chat.completions.create(
            model="gemini-2.5-flash",
            max_tokens=4096,
            stream=True,
            messages=_build_messages(state),
            tools=TOOLS,
        )

        # Accumulate the full response from streamed chunks
        text_content = ""
        tool_calls_by_index: dict[int, dict] = {}
        finish_reason = None

        async for chunk in stream:
            choice = chunk.choices[0] if chunk.choices else None
            if not choice:
                continue

            delta = choice.delta
            finish_reason = choice.finish_reason or finish_reason

            # Stream text tokens to frontend
            if delta and delta.content:
                text_content += delta.content
                await ws_send({
                    "type": "agent_token",
                    "data": {"token": delta.content},
                })

            # Accumulate tool call fragments
            if delta and delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_calls_by_index:
                        tool_calls_by_index[idx] = {
                            "id": tc_delta.id or "",
                            "name": "",
                            "arguments": "",
                        }
                    entry = tool_calls_by_index[idx]
                    if tc_delta.id:
                        entry["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            entry["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            entry["arguments"] += tc_delta.function.arguments

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
