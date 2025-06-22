"""Video generation module using the integrated pipeline."""
import asyncio
import os
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from . import crud, models
from .database import async_session
from .video_pipeline.orchestrator import VideoPipeline
import boto3
from botocore.config import Config
import yaml


# Load configuration
config_path = Path(__file__).parent / "config.yaml"
with open(config_path, 'r') as f:
    CONFIG = yaml.safe_load(f)

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ["AWS_REGION"],
    config=Config(signature_version='s3v4')
)
bucket_name = os.environ["S3_BUCKET"]


async def create_video(dream_id: str):
    """Generate a video for the given dream and upload to S3."""
    
    # Create a new database session for this background task
    async with async_session() as db:
        try:
            print(f"[video.create_video] Starting video generation for dream {dream_id}")
            
            # Get dream data
            dream = await crud.get_dream(db, dream_id)
            if not dream:
                print(f"[video.create_video] Dream {dream_id} not found")
                return
            
            # Build full transcript from segments
            full_transcript = " ".join([
                (seg.transcript or "").strip() 
                for seg in dream.segments
            ]).strip()
            
            if not full_transcript:
                print(f"[video.create_video] No transcript available for dream {dream_id}")
                await crud.set_state(db, dream_id, models.DreamState.completed)
                return
            
            # Also update the dream's transcript field
            dream.transcript = full_transcript
            await db.commit()
            
            # Generate video using the pipeline
            pipeline = VideoPipeline()
            video_path, cost_estimate, metadata = await pipeline.generate_video(
                full_transcript, 
                dream_id
            )
            
            # Upload video to S3
            s3_key = f"dreams/{dream_id}/video.mp4"
            print(f"[video.create_video] Uploading video to S3: {s3_key}")
            
            with open(video_path, 'rb') as f:
                s3_client.upload_file(
                    video_path,
                    bucket_name,
                    s3_key,
                    ExtraArgs={'ContentType': 'video/mp4'}
                )
            
            # Update dream with video information
            dream.video_s3_key = s3_key
            dream.video_metadata = {
                "generated_at": datetime.utcnow().isoformat(),
                "cost_estimate": cost_estimate,
                "metadata": metadata,
                "transcript_length": len(full_transcript),
                "num_segments": len(dream.segments)
            }
            dream.state = models.DreamState.video_generated
            await db.commit()
            
            # Clean up local files
            output_dir = Path(CONFIG["storage"]["local_path"]) / dream_id
            if output_dir.exists():
                import shutil
                shutil.rmtree(output_dir)
            
            print(f"[video.create_video] ✅ Video generation complete for dream {dream_id}")
            print(f"[video.create_video] S3 URL: s3://{bucket_name}/{s3_key}")
            print(f"[video.create_video] Cost estimate: ${cost_estimate:.4f}")
            
        except Exception as e:
            print(f"[video.create_video] ❌ Error generating video for dream {dream_id}: {str(e)}")
            # Update dream state to indicate failure
            dream = await crud.get_dream(db, dream_id)
            if dream:
                dream.state = models.DreamState.completed
                dream.video_metadata = {
                    "error": str(e),
                    "failed_at": datetime.utcnow().isoformat()
                }
                await db.commit()