"""Minimal flow utilising helper functions for tests.
Run: python test_files/mini_flow.py
"""
import pathlib, requests, mimetypes, json, time, sys
from typing import List

API_BASE = "http://localhost:8000"
AUDIO_FILE = pathlib.Path(__file__).parent / "prop33_question2.m4a"

if not AUDIO_FILE.exists():
    sys.exit("Test audio missing")

def create_dream(title: str = "Test Dream") -> str:
    r = requests.post(f"{API_BASE}/dreams/", json={"title": title})
    r.raise_for_status()
    return r.json()["id"]

def upload_and_transcribe(dream_id: str, file_path: pathlib.Path, order: int = 0) -> str:
    filename = file_path.name
    # presigned url
    r = requests.post(f"{API_BASE}/dreams/{dream_id}/upload-url/", params={"filename": filename})
    r.raise_for_status()
    data = r.json()
    # upload
    with file_path.open("rb") as f:
        headers = {"Content-Type": mimetypes.guess_type(filename)[0] or "audio/mpeg"}
        put = requests.put(data["upload_url"], data=f, headers=headers)
        put.raise_for_status()
    # register segment
    payload = {
        "filename": filename,
        "duration": 10.0,
        "order": order,
        "s3_key": data["s3_key"],
    }
    r = requests.post(f"{API_BASE}/dreams/{dream_id}/segments/", json=payload)
    r.raise_for_status()
    return r.json()["transcript"]

def finish_dream(dream_id: str) -> str:
    r = requests.post(f"{API_BASE}/dreams/{dream_id}/finish")
    r.raise_for_status()
    return r.json()["transcript"]

if __name__ == "__main__":
    dream_id = create_dream()
    print("Dream:", dream_id)
    # simulate two clips for demo
    for i in range(2):
        t = upload_and_transcribe(dream_id, AUDIO_FILE, order=i)
        print(f"segment {i} transcript: {t[:60]}…")
    full = finish_dream(dream_id)
    print("\nFULL TRANSCRIPT:\n", full)
