import os
from typing import Callable, Awaitable
import anthropic

from session.state import SessionState
from agent.tools import TOOLS
from agent.system_prompt import SYSTEM_PROMPT
from agent.tool_handlers import handle_tool_call

client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

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


async def run_agent_turn(
    user_message: str,
    state: SessionState,
    ws_send: WsSend,
) -> None:
    """
    Run one full agent turn.

    May involve multiple Claude API calls if Claude uses tools (the agentic loop).
    Streams text tokens to the WebSocket as they arrive for a typewriter effect.
    """
    state.messages.append({"role": "user", "content": user_message})

    while True:
        async with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=_build_system(state),
            messages=state.messages,
            tools=TOOLS,
        ) as stream:
            # Forward text tokens to frontend in real time
            async for event in stream:
                if (
                    event.type == "content_block_delta"
                    and event.delta.type == "text_delta"
                ):
                    await ws_send({
                        "type": "agent_token",
                        "data": {"token": event.delta.text},
                    })

            # Get fully assembled response (tool inputs are complete JSON here)
            final_message = await stream.get_final_message()

        # Append Claude's full response to conversation history
        state.messages.append({
            "role": "assistant",
            "content": final_message.content,
        })

        # No tool calls → Claude is done for this turn
        if final_message.stop_reason != "tool_use":
            await ws_send({"type": "agent_turn_complete", "data": {}})
            return

        # Execute each tool call and collect results
        tool_results = []
        for block in final_message.content:
            if block.type != "tool_use":
                continue

            await ws_send({
                "type": "tool_use",
                "data": {
                    "tool_name": block.name,
                    "tool_input": block.input,
                },
            })

            result_text = await handle_tool_call(
                tool_name=block.name,
                tool_input=block.input,
                state=state,
                ws_send=ws_send,
            )

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_text,
            })

        # Feed tool results back as a user turn (Anthropic protocol)
        state.messages.append({"role": "user", "content": tool_results})
        # Loop: Claude will respond to the tool results, possibly calling more tools
