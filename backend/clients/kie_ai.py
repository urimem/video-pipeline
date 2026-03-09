import asyncio
import json
import logging
import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.kie.ai"
POLL_INTERVAL_SECONDS = 3
MAX_POLLS = 60  # ~3 minutes max wait


class KieAIClient:
    """
    Unified async client for kie.ai job-based APIs.

    Handles the createTask → poll recordInfo pattern used by
    image generation (google/nano-banana) and video generation (kling-3.0/video).
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._http = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    async def close(self):
        await self._http.aclose()

    # ── Low-level helpers ────────────────────────────────────────────

    async def create_task(self, model: str, input_params: dict) -> str:
        """Submit a generation job. Returns the taskId."""
        logger.info(f"Creating task for model: {model} with input params: {input_params}")
        resp = await self._http.post(
            "/api/v1/jobs/createTask",
            json={"model": model, "input": input_params},
        )
        resp.raise_for_status()
        body = resp.json()

        task_id = body.get("data", {}).get("taskId") or body.get("taskId")
        if not task_id:
            raise RuntimeError(f"No taskId in createTask response: {body}")
        return task_id

    async def poll_task(self, task_id: str) -> dict:
        """Poll until the task reaches a terminal state. Returns the full data dict."""
        logger.info(f"Polling task: {task_id}")
        for i in range(MAX_POLLS):
            logger.info(f"Polling task: {task_id} (poll {i+1}/{MAX_POLLS})")
            resp = await self._http.get(
                "/api/v1/jobs/recordInfo",
                params={"taskId": task_id},
            )
            resp.raise_for_status()
            body = resp.json()
            data = body.get("data", {})
            state = data.get("state", "")

            if state == "success":
                return data
            if state == "fail":
                raise RuntimeError(
                    f"Task {task_id} failed: {data.get('failMsg', 'unknown error')}"
                )

            logger.debug("Task %s state=%s (poll %d/%d)", task_id, state, i + 1, MAX_POLLS)
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

        raise TimeoutError(f"Task {task_id} did not complete within {MAX_POLLS * POLL_INTERVAL_SECONDS}s")

    def _parse_result_urls(self, data: dict) -> list[str]:
        """Extract result URLs from the recordInfo response data."""
        logger.info(f"Parsing result URLs from data: {data}")
        result_json_str = data.get("resultJson", "")
        if not result_json_str:
            return []
        result = json.loads(result_json_str)
        # Common patterns: {"resultUrls": [...]}, {"url": "..."}, {"video_url": "..."}
        if isinstance(result, dict):
            if "resultUrls" in result:
                return result["resultUrls"]
            if "url" in result:
                return [result["url"]]
            if "video_url" in result:
                return [result["video_url"]]
        if isinstance(result, list):
            return result
        return []

    # ── Convenience methods ──────────────────────────────────────────

    async def generate_image(
        self,
        prompt: str,
        output_format: str = "png",
        image_size: str = "16:9",
    ) -> dict:
        """
        Generate an image via google/nano-banana.
        Returns: {"task_id": str, "url": str}
        """
        logger.info(f"Generating image with prompt: {prompt}, output format: {output_format}, image size: {image_size}")
        task_id = await self.create_task(
            model="google/nano-banana",
            input_params={
                "prompt": prompt,
                "output_format": output_format,
                "image_size": image_size,
            },
        )
        data = await self.poll_task(task_id)
        urls = self._parse_result_urls(data)
        if not urls:
            raise RuntimeError(f"No image URL in task {task_id} result: {data}")
        return {"task_id": task_id, "url": urls[0]}

    async def generate_video(
        self,
        prompt: str,
        image_url: str,
        duration: int = 5,
    ) -> dict:
        """
        Generate a video via kling-3.0/video (image-to-video).
        Returns: {"task_id": str, "video_url": str}
        """
        logger.info(f"Generating video with prompt: {prompt}, image url: {image_url}, duration: {duration}")
        # TODO:
        logger.info("generate_video called but it is blocked")
        return {"task_id": "generation-blocked", "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}

        task_id = await self.create_task(
            model="kling-3.0/video",
            input_params={
                "prompt": prompt,
                "image_url": image_url,
                "duration": str(duration),
            },
        )
        data = await self.poll_task(task_id)
        urls = self._parse_result_urls(data)
        if not urls:
            raise RuntimeError(f"No video URL in task {task_id} result: {data}")
        return {"task_id": task_id, "video_url": urls[0]}
