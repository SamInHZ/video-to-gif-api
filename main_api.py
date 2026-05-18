import os
import subprocess
import uuid
import time
import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
import httpx
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Paths and directories
TMP_VIDEO_DIR = Path("./tmp_video")
TMP_VIDEO_DIR.mkdir(exist_ok=True)

LOG_DIR = Path("./logs")
LOG_DIR.mkdir(exist_ok=True)


def setup_logger():
    """Configure logging with daily rotated log files."""
    logger = logging.getLogger("video2gif")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    log_file = LOG_DIR / "video2gif.log"
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.suffix = "%Y-%m-%d.log"
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()

GIF_OUTPUT_DIR = TMP_VIDEO_DIR

FILE_EXPIRE_SECONDS = 24 * 60 * 60
CLEANUP_INTERVAL_SECONDS = 60 * 60


def cleanup_old_files():
    """Remove files older than FILE_EXPIRE_SECONDS from TMP_VIDEO_DIR."""
    now = time.time()
    deleted_count = 0

    for file_path in TMP_VIDEO_DIR.iterdir():
        if file_path.is_file():
            file_age = now - file_path.stat().st_mtime
            if file_age > FILE_EXPIRE_SECONDS:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted expired file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete file {file_path}: {e}")

    if deleted_count > 0:
        logger.info(f"Cleanup finished, removed {deleted_count} expired file(s)")
    else:
        logger.debug("No expired files to clean up")


async def periodic_cleanup():
    """Background task that runs cleanup on an interval."""
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        logger.info("Starting scheduled cleanup...")
        cleanup_old_files()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Service started — periodic cleanup enabled (hourly; files older than 24h)"
    )
    cleanup_task = asyncio.create_task(periodic_cleanup())

    cleanup_old_files()

    yield

    logger.info("Service shutting down — stopping periodic cleanup")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Video to GIF Service", lifespan=lifespan)

app.mount(
    "/tmp_video",
    StaticFiles(directory=str(TMP_VIDEO_DIR.resolve())),
    name="gif_files",
)


class VideoRequest(BaseModel):
    url: str
    fps: int = Field(default=5, ge=1, le=60)
    # Relative scale factor (e.g. 0.5 = 50% width and height)
    scale: float = Field(default=0.5, gt=0, le=2.0)


class GifResponse(BaseModel):
    gif_path: str
    message: str


@app.post("/video2gif", response_model=GifResponse)
async def convert_video_to_gif(request: VideoRequest):
    """
    Download a video from **url** and convert it to GIF.

    - **url**: Direct link to the video file
    - **fps**: Output frame rate (default 5)
    - **scale**: Scale relative to source width/height (default 0.5)
    """
    file_id = uuid.uuid4().hex[:8]
    video_path = TMP_VIDEO_DIR / f"{file_id}.mp4"
    gif_path = GIF_OUTPUT_DIR / f"{file_id}.gif"

    start_time = time.time()
    logger.info(
        f"[{file_id}] Convert request — URL: {request.url}, fps: {request.fps}, scale: {request.scale}"
    )

    try:
        logger.info(f"[{file_id}] Downloading video...")
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.get(request.url, follow_redirects=True)
            if response.status_code != 200:
                logger.error(
                    f"[{file_id}] Video download failed, status: {response.status_code}"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Video download failed with status {response.status_code}",
                )
            video_path.write_bytes(response.content)

        video_size = video_path.stat().st_size / 1024 / 1024
        logger.info(f"[{file_id}] Download complete — size: {video_size:.2f} MB")

        logger.info(f"[{file_id}] Converting to GIF...")
        vf = f"fps={request.fps},scale=iw*{request.scale}:ih*{request.scale}"
        gif_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            vf,
            str(gif_path),
        ]

        result = subprocess.run(gif_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"[{file_id}] GIF conversion failed: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"GIF conversion failed: {result.stderr}",
            )

        video_path.unlink()

        gif_size = gif_path.stat().st_size / 1024 / 1024
        elapsed_time = time.time() - start_time
        port = int(os.getenv("PORT", "15999"))
        public_base = os.getenv(
            "PUBLIC_BASE_URL", f"http://127.0.0.1:{port}"
        ).rstrip("/")
        gif_url = f"{public_base}/tmp_video/{gif_path.name}"

        logger.info(
            f"[{file_id}] Success — GIF size: {gif_size:.2f} MB, elapsed: {elapsed_time:.2f}s"
        )

        return GifResponse(
            gif_path=gif_url,
            message="GIF conversion succeeded",
        )

    except httpx.RequestError as e:
        logger.error(f"[{file_id}] Video download failed: {str(e)}")
        raise HTTPException(
            status_code=400, detail=f"Video download failed: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{file_id}] Conversion failed: {str(e)}")
        if video_path.exists():
            video_path.unlink()
        if gif_path.exists():
            gif_path.unlink()
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/cleanup")
async def manual_cleanup():
    """Manually trigger cleanup of expired files under tmp_video."""
    logger.info("Manual cleanup requested")
    cleanup_old_files()
    return {"message": "Cleanup completed"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "15999")))
