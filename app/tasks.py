import httpx, os
VIDEO_SERVICE_URL = os.getenv("VIDEO_SERVICE_URL")

async def enqueue_video_job(dream_id: str):
    """Fire‑and‑forget call to external worker; add retries later."""
    async with httpx.AsyncClient() as client:
        await client.post(VIDEO_SERVICE_URL, json={"dream_id": dream_id})