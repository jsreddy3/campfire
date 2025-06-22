#!/usr/bin/env python3
"""Test video generation for a specific dream"""
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
    # Use the dream ID from your test
    dream_id = "A0591C77-7574-494C-AAB4-00C8C7904201"
    
    print(f"Testing video generation for dream: {dream_id}")
    await create_video(dream_id)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(test_video_generation())