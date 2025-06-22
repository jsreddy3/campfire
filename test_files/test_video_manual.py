#!/usr/bin/env python3
"""Manually test video generation for a specific dream"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to Python path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.video import create_video


async def test_video_generation():
    # Use the dream ID that has segments and transcript
    dream_id = "a0591c77-7574-494c-aab4-00c8c7904201"
    
    print(f"Testing video generation for dream: {dream_id}")
    print("This dream has transcript: 'testing testing testing testing'")
    print("\nStarting video generation...")
    
    try:
        await create_video(dream_id)
        print("\n✅ Video generation completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during video generation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_video_generation())