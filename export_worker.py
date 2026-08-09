from __future__ import annotations

import argparse
from collections import deque
import json
from pathlib import Path
import time
import traceback

import numpy as np
from PIL import Image
import pyvista as pv

from motive_io import load_motive_rigid_body_csv
from rendering.pyvista_helpers import (
    add_body_actors,
    add_room_bounds,
    apply_camera_state,
    set_room_components,
    update_body_actors,
)
from tracking_data import TrackingDataProvider, nearest_sample_index
from video_export import VideoEncodingSettings, finalize_ffmpeg, start_ffmpeg, validate_ffmpeg, write_frame_bytes


class EventLogger:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.file = path.open("w", encoding="utf-8", buffering=1)

    def emit(self, event_type: str, **fields) -> None:
        line = json.dumps({"type": event_type, **fields}, ensure_ascii=False)
        self.file.write(line + "\n")
        print(line, flush=True)

    def log(self, event_type: str, **fields) -> None:
        self.file.write(json.dumps({"type": event_type, **fields}, ensure_ascii=False) + "\n")

    def close(self) -> None:
        self.file.close()


class OffscreenRenderer:
    def __init__(self, data: TrackingDataProvider, config: dict, logger: EventLogger) -> None:
        self.width = int(config["width"])
        self.height = int(config["height"])
        self.ssaa = int(config["ssaa"])
        self.body_settings = data.body_display_settings
        self.geometry_plotter = self._create_plotter(
            (self.width * self.ssaa, self.height * self.ssaa),
            int(config["render_dpi"]),
            int(config["msaa"]),
        )
        self.annotation_plotter = self._create_plotter(
            (self.width, self.height),
            int(config["render_dpi"]),
            int(config["msaa"]),
        )

        logger.log(
            "stage",
            message="Creating off-screen PyVista renderers",
            geometry_size=list(self.geometry_plotter.window_size),
            annotation_size=list(self.annotation_plotter.window_size),
        )

        self.geometry_actors, self.geometry_labels = add_body_actors(
            self.geometry_plotter,
            self.body_settings,
            line_scale=self.ssaa,
        )
        geometry_bounds = add_room_bounds(
            self.geometry_plotter,
            data.room_bounds(),
            line_scale=self.ssaa,
        )
        set_room_components(geometry_bounds, axes=False, grid=True, text=False)

        self.annotation_actors, self.annotation_labels = add_body_actors(
            self.annotation_plotter,
            self.body_settings,
        )
        annotation_bounds = add_room_bounds(self.annotation_plotter, data.room_bounds())
        set_room_components(annotation_bounds, axes=True, grid=False, text=True)

        for plotter in (self.geometry_plotter, self.annotation_plotter):
            apply_camera_state(plotter, config["camera"])
            plotter.show(auto_close=False)

    @staticmethod
    def _create_plotter(size: tuple[int, int], dpi: int, msaa: int) -> pv.Plotter:
        plotter = pv.Plotter(off_screen=True, window_size=size)
        plotter.render_window.SetDPI(dpi)
        plotter.set_background("white")
        if msaa > 1:
            plotter.enable_anti_aliasing("msaa", multi_samples=msaa)
        else:
            plotter.disable_anti_aliasing()
        return plotter

    def set_frame(self, frame) -> float:
        started = time.perf_counter()
        update_body_actors(
            self.geometry_actors,
            self.geometry_labels,
            self.body_settings,
            frame,
        )
        for label in self.geometry_labels.values():
            label.SetVisibility(False)

        update_body_actors(
            self.annotation_actors,
            self.annotation_labels,
            self.body_settings,
            frame,
        )
        for actor in self.annotation_actors.values():
            actor.visibility = False
        return (time.perf_counter() - started) * 1000.0

    @staticmethod
    def _render_and_read(plotter) -> tuple[np.ndarray, float, float]:
        started = time.perf_counter()
        plotter.render_window.Render()
        render_ms = (time.perf_counter() - started) * 1000.0

        started = time.perf_counter()
        image = np.ascontiguousarray(np.asarray(plotter.image, dtype=np.uint8)[:, :, :3])
        readback_ms = (time.perf_counter() - started) * 1000.0
        return image, render_ms, readback_ms

    def capture(self) -> tuple[np.ndarray, dict[str, float]]:
        geometry, geometry_render_ms, geometry_readback_ms = self._render_and_read(self.geometry_plotter)

        downsample_ms = 0.0
        if self.ssaa > 1:
            started = time.perf_counter()
            geometry = np.asarray(
                Image.fromarray(geometry, "RGB").resize(
                    (self.width, self.height),
                    Image.Resampling.LANCZOS,
                ),
                dtype=np.uint8,
            )
            downsample_ms = (time.perf_counter() - started) * 1000.0

        annotation, annotation_render_ms, annotation_readback_ms = self._render_and_read(self.annotation_plotter)

        started = time.perf_counter()
        # The annotation pass is dark text/axes on white. Minimum compositing
        # leaves white pixels untouched while applying the final-resolution
        # annotations over the supersampled geometry/grid image.
        image = np.minimum(geometry, annotation)
        image = np.ascontiguousarray(image)
        composite_ms = (time.perf_counter() - started) * 1000.0

        return image, {
            "geometry_render_ms": geometry_render_ms,
            "geometry_readback_ms": geometry_readback_ms,
            "ssaa_downsample_ms": downsample_ms,
            "annotation_render_ms": annotation_render_ms,
            "annotation_readback_ms": annotation_readback_ms,
            "composite_ms": composite_ms,
        }

    def close(self) -> None:
        self.geometry_plotter.close()
        self.annotation_plotter.close()


def run_export(config: dict, logger: EventLogger) -> None:
    output_path = Path(config["output_path"])
    cancel_path = Path(config["cancel_path"])
    ffmpeg_path = config["ffmpeg_path"]
    codec = config["codec"]
    width = int(config["width"])
    height = int(config["height"])
    fps = int(config["fps"])
    start_s = float(config["start_s"])
    end_s = float(config["end_s"])

    logger.log("stage", message="Validating FFmpeg")
    validate_ffmpeg(ffmpeg_path, codec)

    logger.log("stage", message="Loading Motive CSV")
    session = load_motive_rigid_body_csv(config["csv_path"])
    if not len(session.time):
        raise RuntimeError("The source CSV contains no samples.")

    data = TrackingDataProvider(session)
    if config["smoothing_enabled"]:
        data.ensure_smoothed(float(config["smoothing_seconds"]))

    frame_count = max(1, round(max(0.0, end_s - start_s) * fps) + 1)
    recent = deque(maxlen=30)
    renderer = OffscreenRenderer(data, config, logger)
    process = None
    timing_totals: dict[str, float] = {}

    try:
        settings = VideoEncodingSettings(codec, fps, width, height)
        selected_bodies = config["selected_bodies"]
        smoothing_enabled = bool(config["smoothing_enabled"])
        smoothing_seconds = float(config["smoothing_seconds"])

        for frame_number in range(frame_count):
            if cancel_path.exists():
                raise InterruptedError

            frame_started = time.perf_counter()
            time_s = min(start_s + frame_number / fps, end_s)

            started = time.perf_counter()
            frame = data.scene_frame(
                time_s,
                nearest_sample_index(session.time, time_s),
                selected_bodies,
                smoothing_enabled,
                smoothing_seconds,
            )
            pose_ms = (time.perf_counter() - started) * 1000.0

            scene_update_ms = renderer.set_frame(frame)
            image, timings = renderer.capture()

            if process is None:
                logger.log("stage", message="Starting FFmpeg")
                process = start_ffmpeg(ffmpeg_path, output_path, settings)

            started = time.perf_counter()
            write_frame_bytes(process, image.tobytes(order="C"))
            ffmpeg_ms = (time.perf_counter() - started) * 1000.0
            total_ms = (time.perf_counter() - frame_started) * 1000.0

            frame_timings = {
                "pose_ms": pose_ms,
                "scene_update_ms": scene_update_ms,
                **timings,
                "ffmpeg_ms": ffmpeg_ms,
                "total_ms": total_ms,
            }
            for key, value in frame_timings.items():
                timing_totals[key] = timing_totals.get(key, 0.0) + value

            completed = frame_number + 1
            logger.log("timing", frame=completed, **{key: round(value, 3) for key, value in frame_timings.items()})
            recent.append(total_ms / 1000.0)
            logger.emit(
                "frame",
                current=completed,
                total=frame_count,
                eta=(sum(recent) / len(recent)) * (frame_count - completed),
            )

        return_code, stderr_text = finalize_ffmpeg(process)
        process = None
        if return_code:
            raise RuntimeError(f"FFmpeg exited with code {return_code}.\n{stderr_text}")

        logger.log(
            "timing_average",
            frames=frame_count,
            **{key: round(value / frame_count, 3) for key, value in timing_totals.items()},
        )
        logger.emit("complete", current=frame_count, total=frame_count)

    except InterruptedError:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        output_path.unlink(missing_ok=True)
        logger.emit("cancelled", current=0, total=frame_count)
    except Exception:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        output_path.unlink(missing_ok=True)
        raise
    finally:
        renderer.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    logger = EventLogger(Path(config["log_path"]))
    try:
        run_export(config, logger)
        return 0
    except Exception as exc:
        logger.emit("error", message=f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc())
        return 1
    finally:
        logger.close()


if __name__ == "__main__":
    raise SystemExit(main())
