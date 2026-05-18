# video2gif

A small **HTTP service**: given a direct video URL, it downloads the file, converts it to GIF with **FFmpeg**, and exposes the result via a static mount. Suitable as a portfolio demo.

## Features

- `POST /video2gif` — download video (e.g. mp4), convert to GIF, return a fetchable GIF URL  
- `GET /health` — health check  
- `POST /cleanup` — delete files under `tmp_video` older than 24 hours  
- Hourly scheduled cleanup of stale temp files  

## Requirements

- Python 3.10+ recommended  
- **ffmpeg** installed and on `PATH` (`ffmpeg -version`)

## Quick start

```bash
cd video2gif
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main_api.py
```

Listens on `http://0.0.0.0:15999` by default. Open [Swagger UI](http://127.0.0.1:15999/docs).

### Environment variables (optional)

| Variable | Purpose | Default |
|----------|---------|---------|
| `PORT` | Listen port | `15999` |
| `PUBLIC_BASE_URL` | Prefix for absolute GIF URLs in responses (no trailing `/`) | `http://127.0.0.1:{PORT}` |

Behind a reverse proxy or custom domain, set `PUBLIC_BASE_URL`, for example:

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

Success response:

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

## CLI conversion (optional)

Without running the server:

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
├── requirements.txt      # Runtime deps
├── requirements-dev.txt  # Adds requests for test_api.py
├── README.md
├── .gitignore
├── tmp_video/            # Created at runtime (gitignored)
└── logs/                 # Rotating logs (gitignored)
```

## Publish to GitHub

Create an empty repository on GitHub, then from this folder:

```bash
cd video2gif
git init
git add .
git commit -m "Initial commit: video2gif demo service"
git branch -M main
git remote add origin git@github.com:<your-username>/<your-repo>.git
git push -u origin main
```

Do **not** commit `.env`, `logs/`, `tmp_video/`, or private signed URLs.

## Notes

- GIFs are often much larger than video; lower `fps` and `scale` to reduce size.  
- Video download timeout defaults to 300 seconds; adjust `httpx.AsyncClient(timeout=...)` in `main_api.py` if needed.  
- For production, restrict concurrency, payload size, and allowed origins at the gateway, and tune disk/CPU accordingly.

## License

Add a license file if you need one for your demo.
