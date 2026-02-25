from typing import Callable, Awaitable
from session.state import SessionState, ImageArtifact
from clients.nano_banana import NanaBananaClient
from clients.kling_ai import KlingAIClient

nano_banana = NanaBananaClient()
kling_ai = KlingAIClient()

WsSend = Callable[[dict], Awaitable[None]]


async def handle_tool_call(
    tool_name: str,
    tool_input: dict,
    state: SessionState,
    ws_send: WsSend,
) -> str:
    """Execute a tool call and return a result string for Claude."""

    if tool_name == "update_script":
        state.script = tool_input["script"]
        await ws_send({
            "type": "artifact_update",
            "data": {
                "artifact_type": "script",
                "script": state.script,
            },
        })
        return "Script saved successfully."

    if tool_name == "generate_image":
        img = ImageArtifact(
            type=tool_input["image_type"],
            prompt=tool_input["prompt"],
        )
        state.images.append(img)
        idx = len(state.images) - 1

        await ws_send({
            "type": "artifact_update",
            "data": {
                "artifact_type": "image_pending",
                "index": idx,
                "image_type": img.type,
                "prompt": img.prompt,
            },
        })

        try:
            result = await nano_banana.generate(img.prompt)
            img.url = result["url"]
            img.task_id = result.get("task_id")
            await ws_send({
                "type": "artifact_update",
                "data": {
                    "artifact_type": "image_ready",
                    "index": idx,
                    "image_type": img.type,
                    "url": img.url,
                },
            })
            return f"Image generated successfully: {img.url}"
        except Exception as e:
            return f"Image generation failed: {e}"

    if tool_name == "generate_video":
        await ws_send({
            "type": "artifact_update",
            "data": {"artifact_type": "video_pending"},
        })

        try:
            result = await kling_ai.generate(
                prompt=tool_input["script"],
                duration=tool_input["duration"],
            )
            state.video_url = result["video_url"]
            state.video_task_id = result.get("task_id")
            await ws_send({
                "type": "artifact_update",
                "data": {
                    "artifact_type": "video_ready",
                    "video_url": state.video_url,
                },
            })
            return f"Video generated successfully: {state.video_url}"
        except Exception as e:
            return f"Video generation failed: {e}"

    if tool_name == "update_pipeline_step":
        state.pipeline_step = tool_input["step"]
        await ws_send({
            "type": "pipeline_step_update",
            "data": {"step": state.pipeline_step},
        })
        return f"Pipeline advanced to: {state.pipeline_step}"

    return f"Unknown tool: {tool_name}"
