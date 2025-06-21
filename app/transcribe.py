import os, uuid
import boto3
import httpx
from botocore.config import Config
from sqlalchemy import update, select, func, literal
from .database import async_session
from .models import AudioSegment, Dream

bucket_name = os.getenv("S3_BUCKET")
region      = os.getenv("AWS_REGION", "us-west-2")

s3_client = boto3.client(
    "s3",
    region_name=region,
    config=Config(signature_version="s3v4"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

DG_ENDPOINT = "https://api.deepgram.com/v1/listen"
DG_HEADERS  = {
    "Authorization": f"Token {os.getenv('DEEPGRAM_API_KEY')}",
    "Content-Type": "application/json",
}

async def deepgram_transcribe(presigned_url: str) -> str | None:
    """Send audio URL to Deepgram and get transcript."""
    payload = {"url": presigned_url, "model": "nova-2", "language": "en-US"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(DG_ENDPOINT, headers=DG_HEADERS, json=payload)
        if resp.status_code == 200:
            data = resp.json()
            return data["results"]["channels"][0]["alternatives"][0]["transcript"]
        return None

async def generate_presigned_get(dream_id: str, filename: str) -> str:
    key = f"dreams/{dream_id}/{filename}"
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": key},
        ExpiresIn=3600,
    )

async def transcribe_segment(dream_id: str, segment_id: str, filename: str):
    """Fetch transcript from Deepgram and persist to DB."""
    presigned_url = await generate_presigned_get(dream_id, filename)
    transcript = await deepgram_transcribe(presigned_url)
    if not transcript:
        return None

    # Persist transcript
    async with async_session() as session:
        # update segment transcript
        await session.execute(
            update(AudioSegment)
            .where(AudioSegment.id == uuid.UUID(segment_id))
            .values(transcript=transcript)
        )
        # append to dream transcript atomically
        await session.execute(
            update(Dream)
            .where(Dream.id == uuid.UUID(dream_id))
            .values(
                transcript=func.trim(
                    func.concat(
                        func.coalesce(Dream.transcript, literal("")),
                        literal(" "),
                        literal(transcript)
                    )
                )
            )
        )
        await session.commit()
    return transcript