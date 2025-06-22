#!/usr/bin/env python3
"""Test the integrated API endpoints"""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_integration():
    # 1. Create a dream
    print("1. Creating a dream...")
    response = requests.post(f"{BASE_URL}/dreams/", json={"title": "Test Video Dream"})
    if response.status_code != 201:
        print(f"❌ Failed to create dream: {response.status_code} - {response.text}")
        return
    
    dream = response.json()
    dream_id = dream["id"]
    print(f"✅ Created dream: {dream_id}")
    
    # 2. Check dream details
    print("\n2. Checking dream details...")
    response = requests.get(f"{BASE_URL}/dreams/{dream_id}")
    if response.status_code != 200:
        print(f"❌ Failed to get dream: {response.status_code}")
        return
    
    dream_data = response.json()
    print(f"✅ Dream state: {dream_data['state']}")
    print(f"   Video S3 key: {dream_data.get('video_s3_key', 'None')}")
    print(f"   Video metadata: {dream_data.get('video_metadata', 'None')}")
    
    # 3. Check if video URL endpoint works (will fail since no video yet)
    print("\n3. Testing video URL endpoint...")
    response = requests.get(f"{BASE_URL}/dreams/{dream_id}/video-url/")
    if response.status_code == 404:
        print("✅ Correctly returns 404 when no video exists")
    else:
        print(f"❓ Unexpected response: {response.status_code}")
    
    print("\n✅ Integration test complete!")
    print("\nTo test video generation:")
    print(f"1. Upload audio segments to the dream")
    print(f"2. Call POST /dreams/{dream_id}/finish to trigger video generation")
    print(f"3. Wait for video generation to complete")
    print(f"4. Call GET /dreams/{dream_id}/video-url/ to get the video URL")

if __name__ == "__main__":
    test_integration()