# OptiTrack Motion Workspace

PySide6 workspace for Motive rigid-body data.

## 3D rendering

PyVista / VTK is the only 3D renderer. PyQtGraph is used only by the 2D Signals tab.

Recorded playback and Live use `rendering/pyvista_scene.py`. Shared body, room, text, and camera construction is in `rendering/pyvista_helpers.py`, and Export uses those same helpers.

Current 3D text sizes:

- Axis numbers/titles: 26
- Rigid-body labels: 10

Recorded and Live display renderer diagnostics for target/timer rate, scene-update rate and time, completed render FPS and draw time, preview/DPR/VTK size, and active anti-aliasing.

## Export

Export runs in a separate `export_worker.py` process so a native VTK/driver failure does not close the main workspace.

The Export preview switches to VTK's interactive SSAA whenever the export SSAA setting is above 1x. The exact 2x/3x/4x scale is applied by the off-screen export worker.

Export uses two render passes so SSAA cannot move screen-space annotations:

1. Bodies and room grid render at `output size × SSAA`, then downsample to the requested output resolution.
2. Axis lines/ticks/numbers/titles and rigid-body names render at the final output resolution and are composited over the supersampled geometry.

This keeps annotation size and axis-label/title spacing independent of the export SSAA factor.

Each completed frame also writes detailed timing data to the `.export.log`, including pose calculation, scene update, geometry render, GPU readback, SSAA downsample, annotation render/readback, compositing, FFmpeg write, and total frame time. The Export UI remains limited to the progress bar, completed frames, and estimated time remaining.

Export supports:

- 720p / 1080p / 1440p / 4K
- 15 / 30 / 60 / 120 FPS
- MSAA Off / 2x / 4x / 8x / 16x
- SSAA 1x / 2x / 3x / 4x
- Body selection, smoothing, and time range
- H.264 RGB lossless, FFV1 lossless, H.264 high quality, and H.265 high quality

## Run

```bash
python position_plotter_gui.pyw
```
