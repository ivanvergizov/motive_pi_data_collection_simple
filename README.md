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

Export keeps screen-space annotations independent of SSAA and avoids multiplying MSAA into the supersampled framebuffer:

1. Bodies and room grid render at `output size × SSAA`.
2. At SSAA 1x, selected MSAA applies to geometry normally. Above 1x, the supersampled geometry pass uses MSAA Off and SSAA supplies geometry antialiasing.
3. A GPU shader resolves the geometry to one final-resolution texture. The geometry context then finishes its own work locally before the shared texture is used by the annotation context. No GL sync object is passed between VTK render-window contexts.
4. Axis lines/ticks/numbers/titles and rigid-body names render at final output resolution with the selected MSAA level. The annotation render window shares OpenGL texture resources with the geometry render window.
5. Geometry and annotations are composited on the GPU. The annotation context finishes the composite locally so the geometry texture can be safely reused by the next frame.
6. Only the final 4K RGB frame is read back. That readback uses a three-slot OpenGL Pixel Buffer Object (PBO) ring and fences created/consumed entirely inside the annotation context, so the final GPU-to-CPU transfer can overlap with later work.
7. Completed CPU frames enter the existing three-frame FFmpeg queue so software encoding can overlap with rendering.

The export log records progress, completion, cancellation, and errors. The Export progress panel shows frame progress, ETA, and the completed export duration.

On Windows, the export worker also requests that the system and display stay awake while an export is active to avoid losing the WGL context to normal idle power-off.

Export supports:

- 720p / 1080p / 1440p / 4K
- 15 / 30 / 60 / 120 FPS
- MSAA Off / 2x / 4x / 8x / 16x
- SSAA 1x / 2x / 3x / 4x
- Body selection, smoothing, and time range
- H.264 RGB lossless (MP4)
- H.265 high quality (MP4)

## Run

```bash
python position_plotter_gui.pyw
```

## Rigid-body shape placeholder

`constants.DEFAULT_BODY_TYPE` is the current non-GUI placeholder and is set to `"tetrahedron"`. The renderer also supports `"rectangular_prism"`. `TrackingDataProvider.set_body_type(body_name, body_type)` is the hook intended for a future GUI body-shape control.
