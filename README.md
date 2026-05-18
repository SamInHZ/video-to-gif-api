# Video to GIF API

A small **FastAPI** service: you pass a **direct video URL**, it downloads the file, converts it to a GIF with **FFmpeg**, and returns an HTTP-accessible link to the GIF. Temporary files are cleaned up on a schedule.

## Features

- `POST /video2gif` — download a video (e.g. mp4), convert to GIF, return a fetchable GIF URL in the response  
- `GET /health` — health check  
- `POST /cleanup` — manually remove files under `tmp_video` older than 24 hours  
- Background periodic cleanup (see `main_api.py` for intervals)

## Requirements

- Python 3.10+ recommended  
- **ffmpeg** installed and on your `PATH` (`ffmpeg -version`)

## Quick start

```bash
cd video2gif
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main_api.py
```

Listens on `http://0.0.0.0:15999` by default. API docs: [Swagger UI](http://127.0.0.1:15999/docs).

### Environment variables (optional)

| Variable | Purpose | Default |
|----------|---------|---------|
| `PORT` | Listen port | `15999` |
| `PUBLIC_BASE_URL` | Base URL prefix for absolute GIF links in responses (no trailing `/`) | `http://127.0.0.1:{PORT}` |

Behind a reverse proxy or custom host, set `PUBLIC_BASE_URL`, for example:

```bash
export PUBLIC_BASE_URL=https://your-domain.com
export PORT=15999
python main_api.py
```

GIF URLs look like `{PUBLIC_BASE_URL}/tmp_video/<id>.gif` (served via FastAPI `StaticFiles` from `./tmp_video`).

## API

### `POST /video2gif`

JSON body:

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `url` | string | yes | — | Direct video URL |
| `fps` | int | no | 5 | Roughly 1–60 |
| `scale` | float | no | 0.5 | Relative scale (0.5 ≈ half width and height) |

Example:

```bash
curl -s -X POST "http://127.0.0.1:15999/video2gif" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/demo.mp4","fps":8,"scale":0.5}'
```

Example success response:

```json
{
  "gif_path": "http://127.0.0.1:15999/tmp_video/a1b2c3d4.gif",
  "message": "GIF conversion succeeded"
}
```

### `GET /health`

```bash
curl -s http://127.0.0.1:15999/health
```

### `POST /cleanup`

```bash
curl -s -X POST http://127.0.0.1:15999/cleanup
```

## CLI (no server)

```bash
python video_to_gif.py /path/to/input.mp4 -o out.gif --fps 8 --scale 0.5
```

## Example client script

```bash
pip install -r requirements-dev.txt
export VIDEO_URL="https://example.com/your-video.mp4"
python test_api.py
```

## Layout

```
video2gif/
├── main_api.py           # FastAPI app
├── video_to_gif.py       # Local ffmpeg CLI helper
├── test_api.py           # Sample HTTP client (avoid committing signed/private URLs)
├── requirements.txt
├── requirements-dev.txt  # Extra deps for test_api.py
├── README.md
├── .gitignore
├── tmp_video/            # Created at runtime (gitignored)
└── logs/                 # Rotating logs (gitignored)
```

## Notes

- GIFs are often larger than the source video; lower `fps` and `scale` to reduce size.  
- Video download timeout defaults to 300 seconds; adjust `httpx.AsyncClient(timeout=...)` in `main_api.py` if you need longer.  
- For production, restrict concurrency, payload size, and allowed origins at the gateway, and tune for your CPU and disk.
