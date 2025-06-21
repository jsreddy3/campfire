#!/usr/bin/env python3
"""Example end-to-end flow that:
1. Creates a dream (POST /dreams/)
2. Requests a pre-signed upload URL
3. Uploads a local test audio file to S3 via that URL
4. Registers the segment with the backend (POST /dreams/{id}/segments/)
5. Prints the returned transcript

Run:  python test_files/example_flow.py
Assumes API running locally at http://localhost:8000 and AWS creds / env already configured.
"""
import json, time
import pathlib
import sys
import mimetypes
from uuid import uuid4

import requests

API_BASE = "http://localhost:8000"
AUDIO_PATH = pathlib.Path(__file__).parent / "prop33_question2.m4a"

timings = {}

if not AUDIO_PATH.exists():
    sys.exit(f"Audio file not found: {AUDIO_PATH}")

# 1) Create Dream
start = time.perf_counter()
print("Creating dream …")
resp = requests.post(f"{API_BASE}/dreams/", json={"title": "Test Dream"})
resp.raise_for_status()
end = time.perf_counter()
timings["create_dream"] = end - start
dream = resp.json()
dream_id = dream["id"]
print("Dream id:", dream_id)

filename = AUDIO_PATH.name

# 2) Request presigned upload URL
start = time.perf_counter()
print("Requesting upload URL …")
resp = requests.post(
    f"{API_BASE}/dreams/{dream_id}/upload-url/",
    params={"filename": filename},
)
resp.raise_for_status()
timings["get_upload_url"] = time.perf_counter() - start
up_info = resp.json()
upload_url = up_info["upload_url"]
s3_key     = up_info["s3_key"]
print("Got presigned URL\n→", upload_url[:80], "…")

# 3) Upload file to S3 (PUT)
start = time.perf_counter()
print("Uploading to S3 …")
with AUDIO_PATH.open("rb") as f:
    put_headers = {"Content-Type": mimetypes.guess_type(filename)[0] or "audio/mpeg"}
    put_resp = requests.put(upload_url, data=f, headers=put_headers)
    put_resp.raise_for_status()
timings["upload_s3"] = time.perf_counter() - start
print("Upload successful.")

# 4) Register segment with backend, synchronous transcript
start = time.perf_counter()
print("Registering segment … (this may take a few seconds)")
segment_payload = {
    "filename": filename,
    "duration": 10.0,
    "order": 0,
    "s3_key": s3_key,
}
resp = requests.post(
    f"{API_BASE}/dreams/{dream_id}/segments/", json=segment_payload
)
resp.raise_for_status()
segment = resp.json()
timings["register_segment"] = time.perf_counter() - start
print(json.dumps(segment, indent=2))

print("\nTranscript:\n", segment.get("transcript"))

print("\n=== Timings (seconds) ===")
for k, v in timings.items():
    print(f"{k:20}: {v:.2f}")
print(f"total               : {sum(timings.values()):.2f}")
