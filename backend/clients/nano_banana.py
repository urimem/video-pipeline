import asyncio
import uuid
from typing import Optional


class NanaBananaClient:
    """
    Stub client for Nano Banana image generation API.

    Real API pattern:
      POST /generate            → { task_id }
      GET  /tasks/{task_id}     → { status, image_url }

    To use the real API, replace `_submit_job` and `_poll_result`
    with httpx calls using self.api_key and self.base_url.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.nanobanana.ai",
    ):
        self.api_key = api_key
        self.base_url = base_url

    async def _submit_job(self, prompt: str) -> str:
        """Submit a generation job. Returns task_id."""
        # STUB: simulate submission latency
        await asyncio.sleep(0.1)
        return f"nb_{uuid.uuid4().hex[:8]}"

    async def _poll_result(self, task_id: str) -> dict:
        """Poll until the job completes. Returns result dict."""
        # STUB: simulate ~1.5s processing time
        await asyncio.sleep(1.5)
        return {
            "status": "completed",
            "url": f"https://stub-images.example.com/{task_id}.png",
        }

    async def generate(self, prompt: str) -> dict:
        """
        Full generate flow: submit job then poll until ready.
        Returns: { "task_id": str, "url": str }
        """
        task_id = await self._submit_job(prompt)
        result = await self._poll_result(task_id)
        return {"task_id": task_id, "url": result["url"]}
