#!/usr/bin/env python3
"""CLI helper: convert a local video file to GIF with ffmpeg (no HTTP server)."""

import argparse
import subprocess
import sys
import time


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a video file to GIF using ffmpeg."
    )
    parser.add_argument("video", help="Input video path")
    parser.add_argument(
        "-o",
        "--output",
        default="output.gif",
        help="Output GIF path (default: output.gif)",
    )
    parser.add_argument("--fps", type=int, default=5, help="Frame rate (default: 5)")
    parser.add_argument(
        "--scale",
        type=float,
        default=0.5,
        help="Relative scale factor (default: 0.5, i.e. 50%% width and height)",
    )
    args = parser.parse_args()

    vf = f"fps={args.fps},scale=iw*{args.scale}:ih*{args.scale}"
    cmd = ["ffmpeg", "-y", "-i", args.video, "-vf", vf, args.output]

    print("Running:", " ".join(cmd))
    t0 = time.time()
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        sys.exit(proc.returncode)
    print(f"Done: {args.output} ({time.time() - t0:.2f}s)")


if __name__ == "__main__":
    main()
