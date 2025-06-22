from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import boto3
from botocore.config import Config
from datetime import timedelta
import os

from .database import get_db, Base, engine
from . import crud, schemas, models, s3, tasks, transcribe, video
from fastapi import BackgroundTasks

app = FastAPI(title="Campfire API")

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ["AWS_REGION"],
    config=Config(signature_version='s3v4')
)
bucket_name = os.environ["S3_BUCKET"]


# ─────────────────── Startup ───────────────────
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Auto‑create tables in dev; switch to Alembic migrations later
        await conn.run_sync(Base.metadata.create_all)

# ─────────────────── Routes ───────────────────

@app.get("/list-dreams/", response_model=list[schemas.DreamRead])
async def list_dreams(db: AsyncSession = Depends(get_db)):
    return await crud.list_dreams(db)

@app.get("/dreams/{dream_id}/transcript", response_model=schemas.TranscriptRead)
async def get_dream_transcript(dream_id: str, db: AsyncSession = Depends(get_db)):
    dream = await crud.get_dream(db, dream_id)
    if not dream:
        raise HTTPException(404, "Dream not found")
    return schemas.TranscriptRead(transcript=dream.transcript)

@app.patch("/dreams/{dream_id}", response_model=schemas.DreamRead)
async def update_title(dream_id: str, update: schemas.DreamUpdate, db: AsyncSession = Depends(get_db)):
    dream = await crud.update_title(db, dream_id, update.title)
    if not dream:
        raise HTTPException(404, "Dream not found")
    return dream
    
@app.post("/dreams/", response_model=schemas.DreamRead, status_code=201)
async def create_dream(
    dream: schemas.DreamCreate,
    db: AsyncSession = Depends(get_db),
):
    db_dream = await crud.create_dream(db, dream)
    return db_dream

@app.get("/dreams/{dream_id}", response_model=schemas.DreamRead)
async def read_dream(dream_id: str, db: AsyncSession = Depends(get_db)):
    dream = await crud.get_dream(db, dream_id)
    if not dream:
        raise HTTPException(404, "Dream not found")
    return dream

@app.post("/dreams/{dream_id}/segments/", response_model=schemas.AudioSegmentRead)
async def add_segment(
    dream_id: str,
    seg: schemas.AudioSegmentCreate,
    db: AsyncSession = Depends(get_db),
):
    db_seg = await crud.add_segment(db, dream_id, seg)
    # synchronous transcription (await Deepgram)
    transcript = await transcribe.transcribe_segment(dream_id, str(db_seg.id), db_seg.filename)
    if transcript:
        db_seg.transcript = ((db_seg.transcript or "") + " " + transcript).strip()
    return db_seg

@app.delete("/dreams/{dream_id}/segments/{segment_id}")
async def delete_segment(dream_id: str, segment_id: str, db: AsyncSession = Depends(get_db)):
    seg = await crud.get_segment(db, dream_id, segment_id)
    if not seg:
        raise HTTPException(404, "Segment not found")
    s3_key = seg.s3_key  # capture before deletion/commit
    await crud.remove_segment(db, dream_id, segment_id)
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
    except Exception as e:
        print("S3 delete error", e)
    return {"status": "deleted"}

@app.post("/dreams/{dream_id}/finish")
async def finish_dream(
    dream_id: str,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    dream = await crud.get_dream(db, dream_id)
    if not dream:
        raise HTTPException(404, "Dream not found")
    # schedule video generation (no-op currently)
    background.add_task(video.create_video, dream_id)
    full_transcript = " ".join([(seg.transcript or "").strip() for seg in dream.segments]).strip()
    await crud.set_state(db, dream_id, models.DreamState.completed)
    return {"transcript": full_transcript}


@app.post("/dreams/{dream_id}/video-complete/")
async def video_complete(dream_id: str, db: AsyncSession = Depends(get_db)):
    await crud.set_state(db, dream_id, models.DreamState.completed)
    # TODO: push notification to the user (WebSocket / APNs / FCM)
    return {"status": "ok"}

@app.get("/dreams/{dream_id}/segments/", response_model=list[schemas.AudioSegmentRead])
async def list_segments(
    dream_id: str,
    db: AsyncSession = Depends(get_db),
):
    dream = await crud.get_dream(db, dream_id)
    if not dream:
        raise HTTPException(404, "Dream not found")
    return dream.segments

@app.get("/dreams/{dream_id}/video-url/")
async def get_video_url(dream_id: str, db: AsyncSession = Depends(get_db)):
    """Get a pre-signed URL for downloading the video"""
    dream = await crud.get_dream(db, dream_id)
    if not dream:
        raise HTTPException(404, "Dream not found")
    
    if not dream.video_s3_key:
        raise HTTPException(404, "Video not found for this dream")
    
    # Generate pre-signed URL valid for 1 hour
    presigned_url = s3_client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': bucket_name,
            'Key': dream.video_s3_key,
        },
        ExpiresIn=3600  # 1 hour
    )
    
    return {
        "video_url": presigned_url,
        "expires_in": 3600,
        "metadata": dream.video_metadata
    }

@app.post("/dreams/{dream_id}/upload-url/")
async def get_upload_url(dream_id: str, filename: str):
    """Generate a pre-signed URL for uploading to S3"""
    s3_key = f"dreams/{dream_id}/{filename}"
    
    # Generate pre-signed URL valid for 10 minutes
    presigned_url = s3_client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': bucket_name,
            'Key': s3_key,
        },
        ExpiresIn=600  # 10 minutes
    )
    
    return {
        "upload_url": presigned_url,
        "s3_key": s3_key
    }