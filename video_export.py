from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess


@dataclass(frozen=True)
class VideoEncodingSettings:
    codec_name: str
    fps: int
    width: int
    height: int


_ENCODERS = {
    "H.264 RGB lossless (MP4)": "libx264rgb",
    "FFV1 lossless (MKV)": "ffv1",
    "H.264 high quality (MP4)": "libx264",
    "H.265 high quality (MP4)": "libx265",
}


def find_ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


def output_extension(codec_name: str) -> str:
    return ".mkv" if codec_name.startswith("FFV1") else ".mp4"


def validate_ffmpeg(ffmpeg_path: str, codec_name: str) -> None:
    encoder = _ENCODERS[codec_name]
    probe = subprocess.run(
        [ffmpeg_path, "-hide_banner", "-h", f"encoder={encoder}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=10,
    )
    if probe.returncode or f"Encoder {encoder} " not in probe.stdout:
        raise RuntimeError(f"This FFmpeg build does not provide {encoder}.")


def build_ffmpeg_command(
    ffmpeg_path: str,
    output_path: str | Path,
    settings: VideoEncodingSettings,
) -> list[str]:
    command = [
        ffmpeg_path,
        "-y",
        "-hide_banner",
        "-loglevel", "error",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{settings.width}x{settings.height}",
        "-r", str(settings.fps),
        "-i", "-",
        "-an",
    ]

    if settings.codec_name == "H.264 RGB lossless (MP4)":
        command += [
            "-c:v", "libx264rgb",
            "-crf", "0",
            "-preset", "medium",
            "-pix_fmt", "rgb24",
            "-movflags", "+faststart",
        ]
    elif settings.codec_name == "FFV1 lossless (MKV)":
        command += [
            "-c:v", "ffv1",
            "-level", "3",
            "-coder", "1",
            "-context", "1",
            "-g", "1",
            "-slicecrc", "1",
        ]
    elif settings.codec_name == "H.264 high quality (MP4)":
        command += [
            "-c:v", "libx264",
            "-crf", "12",
            "-preset", "slow",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
        ]
    elif settings.codec_name == "H.265 high quality (MP4)":
        command += [
            "-c:v", "libx265",
            "-crf", "14",
            "-preset", "slow",
            "-pix_fmt", "yuv420p",
            "-tag:v", "hvc1",
            "-movflags", "+faststart",
        ]
    else:
        raise ValueError(f"Unknown codec preset: {settings.codec_name!r}")

    command.append(str(output_path))
    return command


def start_ffmpeg(
    ffmpeg_path: str,
    output_path: str | Path,
    settings: VideoEncodingSettings,
) -> subprocess.Popen:
    return subprocess.Popen(
        build_ffmpeg_command(ffmpeg_path, output_path, settings),
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        bufsize=0,
    )


def ffmpeg_error_text(process: subprocess.Popen) -> str:
    return process.stderr.read().decode("utf-8", errors="replace").strip()


def write_frame_bytes(process: subprocess.Popen, frame_bytes: bytes) -> None:
    if process.poll() is not None:
        message = ffmpeg_error_text(process)
        raise RuntimeError(
            f"FFmpeg exited before accepting the next frame (code {process.returncode})."
            + (f"\n{message}" if message else "")
        )

    view = memoryview(frame_bytes)
    written = 0
    while written < len(view):
        count = process.stdin.write(view[written:])
        if not count:
            raise RuntimeError("FFmpeg stopped accepting frame data.")
        written += count
    process.stdin.flush()


def finalize_ffmpeg(process: subprocess.Popen) -> tuple[int, str]:
    process.stdin.close()
    return_code = process.wait()
    return return_code, ffmpeg_error_text(process)
