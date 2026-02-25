import asyncio
import uuid
from typing import Optional

POLL_INTERVAL_SECONDS = 3
MAX_POLLS = 20  # ~60 seconds max wait


class KlingAIClient:
    """
    Stub client for Kling AI video generation API.

    Real API pattern:
      POST /v1/videos/text2video              → { data: { task_id } }
      GET  /v1/videos/text2video/{task_id}    → { data: { task_status, works: [{ resource_list }] } }

    Kling AI task statuses: "submitted" | "processing" | "succeed" | "failed"
    Auth: JWT Bearer token (derived from api_key + secret).

    To use the real API, replace `_submit_job` and `_poll_until_complete`
    with httpx calls using self.api_key and self.base_url.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.klingai.com",
    ):
        self.api_key = api_key
        self.base_url = base_url

    async def _submit_job(self, prompt: str, duration: int) -> str:
        """Submit text-to-video job. Returns task_id."""
        # STUB: simulate submission latency
        await asyncio.sleep(0.2)
        return f"kling_{uuid.uuid4().hex[:8]}"

    async def _poll_until_complete(self, task_id: str) -> dict:
        """
        Poll task status until complete or timeout.
        Returns result dict with video_url on success.
        """
        for _ in range(MAX_POLLS):
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            # STUB: resolve immediately on first poll
            return {
                "status": "succeed",
                "video_url": f"https://stub-videos.example.com/{task_id}.mp4",
            }
        raise TimeoutError(f"Kling AI task {task_id} did not complete in time")

    async def generate(self, prompt: str, duration: int = 5) -> dict:
        """
        Full generate flow: submit then poll until complete.
        Returns: { "task_id": str, "video_url": str }
        """
        if duration not in (5, 10):
            raise ValueError("Duration must be 5 or 10 seconds")

        task_id = await self._submit_job(prompt, duration)
        result = await self._poll_until_complete(task_id)

        if result["status"] != "succeed":
            raise RuntimeError(f"Kling AI generation failed with status: {result['status']}")

        return {"task_id": task_id, "video_url": result["video_url"]}
