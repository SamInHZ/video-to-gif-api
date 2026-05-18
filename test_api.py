"""Example client for the Video2GIF API (set VIDEO_URL to a reachable mp4 URL)."""

import os

import requests

BASE = os.getenv("API_BASE", "http://127.0.0.1:15999")
url = f"{BASE.rstrip('/')}/video2gif"
headers = {"Content-Type": "application/json"}
data = {
    "url": os.getenv(
        "VIDEO_URL",
        "https://example.com/path/to/video.mp4",
    ),
    "fps": 8,
    "scale": 0.5,
}

response = requests.post(url, json=data, headers=headers)

print("Status:", response.status_code)
if response.status_code == 200:
    print("Body:", response.json())
else:
    print("Error:", response.text)
