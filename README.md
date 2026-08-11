# Motion Tracking Workspace

PySide6 desktop application for Motive rigid-body CSV analysis. It provides 2D signal plots, recorded 3D playback, a prepared Live workspace, and GPU-accelerated video export.

## Basic user instructions

The project root contains only files a normal user may need to run, install from, or edit:

- `position_plotter_gui.pyw` — **run this to start the application**. On Windows, double-click it or run `py position_plotter_gui.pyw`.
- `requirements.txt` — Python dependencies. The launcher checks dependencies on startup and offers to install missing/broken packages. Manual installation is `py -m pip install -r requirements.txt`.
- `rigid_body_types.csv` — **edit this to map Motive rigid-body names to visual body types**.
- `README.md` — this documentation.

FFmpeg is also required for video export. If `ffmpeg.exe` is on `PATH`, the Export tab detects it. Otherwise use the Export tab's FFmpeg **Browse** button and select the actual executable.

### Rigid-body type mapping

`rigid_body_types.csv` currently contains:

```csv
rigid_body_name,body_type
Tablet,tablet
Mobile,mobile
Mobile Phone,mobile
TestRigid1,raspberry_pi
```

Rigid-body names are case-sensitive and must exactly match the names in the Motive CSV. Body-type values remain lowercase.

Available body types:

- `tetrahedron` — fallback for every body name that is not listed in the CSV.
- `raspberry_pi` — 0.090 m long × 0.065 m wide × 0.025 m thick.
- `tablet` — 0.270 m long × 0.195 m wide × 0.0125 m thick.
- `mobile` — 0.135 m long × 0.0975 m wide × 0.0125 m thick.

Dimensions are defined once in `motion_app/geometry/body_geometry.py`. Renderers ask for a body type; they do not carry duplicate body dimensions through the application.

### 3D visual settings

Shared visual settings are in `motion_app/rendering/scene_style.py`.

Current important values:

```python
REFERENCE_DPI = 72.0
REFERENCE_VIEWPORT_HEIGHT_DIP = 1080.0
AXIS_TEXT_HEIGHT_DIP_AT_REFERENCE = 12.0
BODY_LABEL_FONT_SIZE_PT_AT_REFERENCE = 15.0
ROOM_VERTICAL_CAMERA_SHIFT_FRACTION = 1.0 / 8.0
```

Recorded 3D, Live, and the Export-tab preview all use the top-toolbar **Preview AA** setting. The Export tab's resolution/MSAA/SSAA controls affect the **final video only**, not its interactive preview.

Interactive annotation sizing follows the Qt/VTK device-pixel-ratio model. Export uses a monitor-independent virtual DPI based on output height so exported text proportions do not depend on the monitor attached to the computer doing the export.

### Video export

The two output codecs are:

- `H.264 RGB lossless (MP4)` — exact RGB output using `libx264rgb`.
- `H.265 high quality (MP4)` — smaller lossy HEVC output.

Export progress shows completed frames, ETA, and final completion time. Persistent `.export.log` files are not created.

---

# Project structure

Nothing inside `motion_app/` is intended to be launched directly by a normal user.

## Root files

### `position_plotter_gui.pyw`

Application launcher.

- `main()` — creates the Qt application, constructs `WorkspaceMainWindow`, shows it, and enters the event loop.
- Before `main()`, `ensure_dependencies_or_exit()` verifies dependencies.

### `requirements.txt`

Package installation list. No minimum-version constraints are enforced.

### `rigid_body_types.csv`

User-editable rigid-body-name → body-type mapping. Unlisted names use `tetrahedron`.

---

## `motion_app/core/`

Data types, CSV loading, coordinate math, smoothing, playback state, room calculations, and shared non-rendering constants.

### `app_types.py`

Shared type aliases and dataclasses.

- `PlotSignalSelection` — one selected body/signal pair for 2D plotting.
- `CurveSpec` — complete plotted-curve data and styling.
- `BodyDisplaySettings` — body type and display color.
- `BodyPose` — one body's position and quaternion for a frame.
- `SceneFrame` — all visible body poses and frame metadata.
- `RoomBounds` — room extents and tick spacing.
  - `center()` — XYZ center.
  - `spans()` — XYZ extents.
  - `as_sequence()` — bounds in VTK/PyVista order.

### `body_config.py`

Rigid-body type configuration.

- `DEFAULT_BODY_TYPE` — fallback type, `tetrahedron`.
- `BODY_TYPE_FILE` — root `rigid_body_types.csv` path.
- `load_body_type_map()` — validates and loads exact body-name mappings.

### `constants.py`

Signal definitions, plot colors, preview AA choices, export resolution/AA choices, and codec labels.

- `color_for_curve()` — cycles through the common color palette.
- `parse_preview_aa()` — converts the toolbar label into the internal AA mode/sample count.

### `motive_io.py`

Motive rigid-body CSV parsing.

- `RigidBodyData` — interpolated and pre-interpolation position/rotation arrays for one rigid body.
- `TrackingSession` — frames, timestamps, rigid bodies, and source rotation encoding.
- `find_rotation_encoding()` — determines Euler vs quaternion source rotation columns.
- `load_motive_rigid_body_csv()` — parses a Motive CSV and returns a `TrackingSession`.

### `playback_controller.py`

Wall-clock playback state for Recorded 3D.

- `PlaybackController.__init__()` — initializes time state.
- `is_playing` — current playback state.
- `duration_s` — session duration.
- `set_time_array()` — installs timestamps and resets playback.
- `set_speed()` — changes playback multiplier.
- `play()` / `pause()` — start or stop playback.
- `seek()` — moves to a requested time.
- `sample()` — returns current playback time and nearest sample.
- `_restart_origin()` — re-anchors wall-clock timing.
- `_update_from_wall_clock()` — advances playback from real elapsed time.

### `rigid_body_math.py`

Coordinate/orientation conversions.

- `motive_positions_to_display()` — Motive XYZ → display coordinates.
- `quaternion_xyzw_to_motive_rotation_matrix()` — Motive-space quaternion rotation matrix.
- `quaternion_xyzw_to_rotation_matrix()` — display-space rotation matrix.
- `xyz_degrees_to_quaternion_xyzw()` — Euler XYZ degrees → quaternion.
- `quaternion_xyzw_to_xyz_degrees()` — quaternion → Euler XYZ degrees.

### `room_geometry.py`

Room extents and tick spacing.

- `nice_tick_spacing()` — selects readable 1/2/5-style spacing.
- `calculate_room_axis_bounds()` — padded min/max/tick values for one axis.
- `calculate_room_bounds()` — complete 3D bounds from tracked positions.

### `signal_processing.py`

Missing-value handling and optional smoothing.

- `fill_missing_values()` — fills gaps in numeric signals.
- `estimate_sample_rate_hz()` — estimates sample rate from timestamps.
- `smoothing_seconds_to_window_size()` — seconds → odd smoothing-window size.
- `smooth_values_centered()` — centered smoothing for general arrays.
- `smooth_positions_centered()` — XYZ smoothing.
- `normalize_quaternions()` — row-wise quaternion normalization.
- `make_quaternion_signs_continuous()` — removes equivalent quaternion sign flips.
- `smooth_quaternions_centered()` — smooths and renormalizes quaternion data.
- `smooth_tracking_positions_and_rotations()` — coordinated position/quaternion smoothing.

### `tracking_data.py`

Central session-to-view data provider.

- `nearest_sample_index()` — nearest timestamp index.
- `TrackingDataProvider.__init__()` — initializes caches and optional session.
- `set_session()` — converts data, reads body mappings, assigns colors/types, and resets caches.
- `set_body_type()` — programmatic future hook for changing a body's type.
- `clear_smoothing_cache()` — clears all smoothing-derived arrays.
- `ensure_smoothed()` — computes/caches one smoothing duration.
- `positions()` / `rotations()` — raw or smoothed display data.
- `room_bounds()` — calculates padded room bounds using the largest configured body.
- `scene_frame()` — creates one renderable `SceneFrame`.
- `signal_values()` — returns raw/interpolated/smoothed 2D signals.
- `_interpolated_signal()` / `_raw_signal()` — internal signal selectors.
- `_require_session()` — validates that a session is loaded.

---

## `motion_app/geometry/`

Rigid-body dimensions and mesh generation.

### `body_geometry.py`

- `BodyDimensions` — length, width, height.
  - `max_dimension` — largest side.
- `body_dimensions()` — central lookup for a body type's dimensions.
- `create_body_geometry()` — tetrahedron or rectangular-prism vertices/faces for the selected body type.

---

## `motion_app/rendering/`

Shared PyVista/VTK rendering for interactive views and export.

### `scene_style.py`

Single source of visual constants: DPI reference, annotation sizes/offsets, axis/grid colors, camera view angle, and vertical camera shift.

### `pyvista_helpers.py`

Shared scene/annotation/camera helpers.

- `sync_interactive_dpi()` — synchronizes the VTK render-window DPI with Qt's device-pixel ratio and returns DPI/DPR.
- `export_render_dpi()` — monitor-independent virtual DPI for an exported frame.
- `_viewport_scale()` — derives viewport/device-pixel scaling for annotations.
- `apply_annotation_viewport_style()` — applies shared DPI/viewport-aware axis and body-label sizes.
- `_default_camera_values()` — shared default camera position/focal point.
- `_add_body_label()` — creates one billboard label.
- `add_body_labels()` — creates all configured labels.
- `add_body_actors()` — creates all rigid-body mesh actors.
- `add_room_bounds()` — creates room axes/grid/ticks/text.
- `set_room_components()` — chooses which room components are visible in a render pass.
- `update_body_actors()` — updates mesh transforms/visibility.
- `update_body_labels()` — updates label positions/visibility.
- `frame_camera()` — applies default framing.
- `camera_state()` — serializes current camera.
- `apply_camera_state()` — restores serialized camera state.

### `pyvista_scene.py`

Reusable interactive `QtInteractor` scene used by Recorded 3D, Live, and Export preview.

- `PyVistaRigidBodyScene.__init__()` — initializes the scene and GUI-visible performance history.
- `_create_plotter()` — creates the `QtInteractor`, applies DPI and preview AA.
- `_sync_annotation_style()` — reapplies annotation style only when viewport/DPI signature changes.
- `resizeEvent()` — updates annotation sizing after viewport resize.
- `configure_bodies()` — rebuilds body meshes/labels from display settings.
- `set_room_bounds()` — installs room visuals and default camera.
- `set_frame()` — updates body/label pose and update metrics.
- `request_render()` — renders and records GUI-visible render timing.
- `set_anti_aliasing()` — rebuilds the interactive renderer while preserving scene/camera state.
- `actual_anti_aliasing_text()` — reports actual VTK AA state.
- `export_camera_state()` — current camera for video export.
- `reset_metrics()` — clears GUI-visible performance history.
- `_rate()` — events-per-second helper.
- `metrics_text()` — text shown in Recorded/Live diagnostics panels.
- `shutdown()` — closes VTK/PyVista resources.
- `_remove_bodies()` — removes existing actors/labels before rebuilding.

---

## `motion_app/exporting/`

Video export helpers and the isolated GPU export worker. The worker is launched by the Export tab and should not be run manually.

### `video_export.py`

FFmpeg and shared export calculations.

- `VideoEncodingSettings` — codec/FPS/width/height passed to FFmpeg.
- `export_frame_count()` — **single shared inclusive frame-count calculation** used by both the Export GUI and worker.
- `_creation_flags()` — Windows no-console subprocess flag.
- `is_ffmpeg_executable()` — verifies a path actually runs FFmpeg.
- `find_ffmpeg()` — searches `PATH` and accepts only a runnable FFmpeg.
- `validate_ffmpeg()` — verifies the required encoder exists.
- `build_ffmpeg_command()` — constructs H.264 RGB lossless or H.265 high-quality command.
- `start_ffmpeg()` — starts FFmpeg with raw RGB stdin.
- `ffmpeg_error_text()` — reads encoder stderr.
- `write_frame_bytes()` — writes one complete frame to FFmpeg.
- `finalize_ffmpeg()` — closes input, waits, and returns status/error text.

### `export_worker.py`

Isolated process for GPU rendering. Keeping it separate prevents a native VTK/OpenGL crash from taking down the GUI.

- `EventEmitter` — sends progress/completion/error JSON to the GUI through stdout; no persistent export log is created.
- `WindowsExecutionState` — prevents display/system sleep during active export.
- `GpuGeometryResolve` — GPU framebuffer/texture/shader for SSAA downsampling.
  - `resolve()` — downsamples high-resolution geometry to final resolution and synchronizes locally.
  - `close()` — frees resolve resources.
- `_ReadbackSlot` — one asynchronous PBO slot.
- `AsyncGpuCompositor` — combines geometry + annotations on-GPU and downloads final frames through a PBO ring.
  - `_pointer_address()` — mapped-pointer conversion.
  - `_wait_for_slot()` — waits only when a readback slot must be reused.
  - `_collect_oldest()` — maps/copies/releases the oldest completed slot.
  - `collect_ready()` — retrieves ready slots without unnecessary blocking.
  - `submit()` — composites and starts an asynchronous readback.
  - `flush()` — drains outstanding readbacks.
  - `close()` — frees PBO/fence/FBO/shader resources.
- `OffscreenRenderer` — coordinates the two VTK render passes.
  - `__init__()` — computes room bounds **once**, creates both passes, camera, shared resources, resolve stage, and compositor.
  - `_create_plotter()` — creates one off-screen PyVista plotter with requested size/MSAA.
  - `_set_camera()` — applies shared room framing or exported camera state.
  - `set_frame()` — updates body geometry and labels.
  - `submit_frame()` — renders geometry, resolves SSAA, renders annotations, composites, and submits readback.
  - `flush()` — gets remaining frames.
  - `close()` — frees GPU/render-window resources.
- `QueuedFFmpegWriter` — background writer that lets FFmpeg consume completed frames while rendering continues.
  - `_run()` — writes frames and emits progress/ETA.
  - `submit()` — queues one completed frame.
  - `finish()` — drains and finalizes encoder.
  - `abort()` — terminates encoder/writer after cancellation/error.
- `run_export()` — loads the source CSV, calculates the shared frame count, renders frames, handles cancellation, and emits completion time.
- `main()` — reads temporary config, keeps Windows awake, runs export, and reports exceptions.

### Export AA pipeline

When SSAA > 1, the export intentionally does **not** place MSAA on the supersampled geometry framebuffer:

1. Bodies/grid render at output resolution × selected SSAA; geometry MSAA is off.
2. GPU shader downsamples geometry to final resolution.
3. Axes/ticks/body names render at final resolution with selected MSAA.
4. GPU shader composites the two passes.
5. One final RGB image is downloaded through a 3-slot asynchronous PBO ring.
6. A separate 3-frame CPU queue feeds FFmpeg.

This avoids the old SSAA × MSAA VRAM multiplication while retaining both controls for their intended passes.

---

## `motion_app/ui/`

Main window, workspace tabs, plotting widget, and reusable controls.

### `main_window.py`

- `WorkspaceMainWindow.__init__()` — tabbed window, toolbar, initial Signals workspace.
- `_create_toolbar()` — New tab, global Preview AA, status, and close-tab controls.
- `create_workspace()` — opens Signals, Recorded 3D, Live, or Export.
- `handle_global_aa_changed()` — sends toolbar AA to all open 3D previews.
- `verify_global_anti_aliasing()` — reports requested vs actual AA.
- `close_current_workspace()` / `close_workspace_tab()` — closes workspaces.
- `_shutdown_workspace()` — calls tab-specific cleanup when available.
- `closeEvent()` — shuts down all workspaces before application exit.

### `plotting/multi_axis_signal_plot.py`

- `MultiAxisSignalPlot.__init__()` — PyQtGraph plot with position/Euler/quaternion Y axes.
- `_create_axes()` — constructs linked axes/view boxes.
- `_sync_viewboxes()` — keeps view boxes geometrically aligned.
- `set_x_range()` — time-axis range.
- `set_curves()` — redraws selected curves.
- `clear()` — removes curves.
- `has_data()` — whether a signal type has data.
- `set_axis_scale()` — vertical scale multiplier.
- `_calculate_ranges()` — base data ranges.

### `tabs/signal_plot_tab.py`

- `SignalPlotTab.__init__()` — Signals workspace.
- `_build_layout()` — sidebar + plot.
- `_create_axis_scale_group()` — vertical scaling controls.
- `_connect_signals()` — UI signal wiring.
- `load_csv()` — Motive CSV load.
- `set_session()` — installs loaded data and initializes controls.
- `_mode()` — raw/interpolated/smoothed selection.
- `_handle_smoothing_changed()` / `_handle_mode_changed()` — redraw logic.
- `_update_smoothing_state()` — calls the smoothing widget's single `set_available()` API.
- `update_plot()` — obtains current curves and redraws.
- `_update_status()` — source/session text.

### `tabs/recorded_3d_tab.py`

- `Recorded3DPlaybackTab.__init__()` — playback controls, scene, timers, GUI diagnostics.
- `_build_layout()` — sidebar + 3D view.
- `_connect_signals()` — file/body/smoothing/playback/render wiring.
- `load_csv()` — loads Motive data.
- `set_session()` — installs body mappings, room, playback timeline, smoothing availability.
- `_play()` / `_pause()` / `_seek()` — playback commands.
- `_set_render_fps()` — requested render cadence.
- `_render_tick()` — wall-clock render scheduling.
- `_render_frame()` — builds and renders current `SceneFrame`.
- `_refresh_scene()` — redraws current sample.
- `_update_metrics()` — GUI-visible renderer metrics.
- `set_global_anti_aliasing()` — applies toolbar Preview AA.
- `shutdown()` — stops timers and renderer.

### `tabs/live_tab.py`

Live-network transport is still a placeholder; renderer/settings UI is prepared for later integration.

- `LivePlaybackTab.__init__()` — placeholder connection controls, smoothing, render settings, metrics, 3D scene.
- `_build_layout()` — sidebar + scene.
- `_create_connection_group()` — bind/port/start/stop/record controls.
- `_update_metrics()` — GUI-visible renderer metrics.
- `set_global_anti_aliasing()` — applies toolbar Preview AA.
- `shutdown()` — stops timer and renderer.

### `tabs/export_tab.py`

Export-tab GUI and process orchestration. Heavy rendering and encoding algorithms live in `export_worker.py` / `video_export.py`; this file owns the user-facing state and worker lifecycle.

- `_console_python()` — uses console `python.exe` instead of `pythonw.exe` for worker launch when available.
- `_duration_text()` — formats ETA/completion time.
- `ExportTab.__init__()` — creates controls, preview, progress state, and worker state.
- `_build_layout()` / `_create_*_group()` — builds sidebar sections.
- `_connect_signals()` — UI wiring.
- `load_source_csv()` / `set_session()` — loads and installs export source data.
- `_update_preview()` — renders the Export-tab preview at the selected start time; preview AA comes from the top toolbar.
- `_select_ffmpeg()` / `_update_ffmpeg_status()` — FFmpeg selection and status.
- `select_output_file()` / `_set_output_label()` — output path selection/display.
- `_validate_time_range()` / `_update_export_button()` — export readiness.
- `start_export()` — validates config, uses shared `export_frame_count()`, writes temporary worker config, and launches isolated worker.
- `_read_worker_stdout()` / `_read_worker_stderr()` — worker communication.
- `_handle_worker_event()` — progress/ETA/completion UI updates.
- `_worker_process_error()` / `_worker_finished()` — process termination handling.
- `cancel_export()` / `_force_kill_worker()` — cooperative then forced cancellation.
- `_cleanup_worker_files()` — deletes temporary config/cancel markers.
- `_show_failure()` — user error dialog.
- `_set_configuration_enabled()` — locks/unlocks settings while exporting.
- `set_global_anti_aliasing()` — applies top-toolbar Preview AA to the interactive preview only.
- `shutdown()` — terminates worker and closes preview safely.

### `widgets/body_selection.py`

- `BodySelectionWidget.__init__()` — body checkboxes.
- `set_bodies()` — rebuilds checkbox list.
- `selected_names()` — selected body names.

### `widgets/playback_controls.py`

- `PlaybackControlsWidget.__init__()` — play/pause/timeline/speed/current frame controls.
- `set_duration()` — timeline range/state.
- `set_time()` — current playback labels.

### `widgets/render_settings.py`

- `RenderSettingsWidget.__init__()` — FPS and optional export resolution/MSAA/SSAA controls.
- `fps()` — selected FPS.
- `msaa_samples()` — selected MSAA count.
- `ssaa_factor()` — selected SSAA factor.
- `resolution()` — selected export dimensions.

### `widgets/session_source.py`

- `SessionSourceWidget.__init__()` — CSV Browse + source status.
- `set_status()` — status text.
- `_select_file()` — file chooser and selected-path signal.

### `widgets/signal_selection.py`

- `SignalSelectionWidget.__init__()` — body/signal tree.
- `set_bodies()` — rebuilds tree.
- `selections()` — checked selections.
- `_new_signal_item()` — creates checkable signal item.
- `_handle_item_changed()` — parent/child check-state handling and signal emission.

### `widgets/smoothing_controls.py`

- `SmoothingControlsWidget.__init__()` — smoothing checkbox + window control.
- `enabled` — whether smoothing is selected.
- `seconds` — smoothing duration.
- `set_available()` — **single public availability API** that enables/disables the group and restores the duration control appropriately.
- `_emit_settings()` — updates duration-control state and emits current settings.

---

## `motion_app/support/`

Startup-only support.

### `dependency_check.py`

- `DEPENDENCY_IMPORTS` — single Python package → representative import mapping used both to check dependencies and build the pip install command. There is no separate duplicate package list.
- `_python_executable()` — console Python when launcher is using `pythonw.exe`.
- `_missing_dependencies()` — imports each representative module and records failures.
- `_dialog()` — PySide6 dependency dialog with tkinter fallback.
- `ensure_dependencies_or_exit()` — offers to install/repair dependencies and exits for restart afterward.

### Startup behavior

The launcher currently performs a **full import check of every dependency on every startup** before the main window is created. This deliberately tests that the packages are not merely installed but actually import successfully. The expensive imports include NumPy, pandas, PySide6, PyQtGraph, PyVista, PyVistaQt, VTK, and PyOpenGL.

After that, `WorkspaceMainWindow` is imported. Its module imports all workspace-tab modules, so the plotting/rendering modules are also loaded before the first window appears. Python caches modules already imported by the dependency check, but the dependency check itself means the full 3D stack is initialized even if the user initially opens only the Signals tab.

The main window then creates only the **Signals** workspace. Recorded/Live/Export `QtInteractor` OpenGL render windows are not created until those tabs are opened.

This eager dependency validation is the most likely reason startup feels slow. It is intentionally conservative, not required for normal runtime speed. A future startup optimization could use a cheaper package-presence check and/or lazy-import 3D workspace modules only when opened, while retaining a clear error path if a dependency fails to import at that point.

---

## `tests/`

Developer tests and fixture data. Normal users do not need to run them.

### `test_core.py`

- `make_body()` — synthetic rigid-body test data.
- `CoreTests` — coordinate conversion, signals, scene frames, body mapping/fallback, body dimensions, config CSV parsing, nearest sample, room bounds.
- `VideoExportCommandTests` — FFmpeg command tests plus the shared inclusive export-frame-count test.

Run manually:

```powershell
py -m unittest -v tests.test_core
```

### `test2.csv`

Small Motive CSV fixture used for development/manual testing.

---

# Design notes

## Why `export_tab.py` is still relatively large

`export_worker.py` performs the GPU rendering and `video_export.py` owns FFmpeg details, but `export_tab.py` still has to own all GUI-side export responsibilities:

- constructing the Export settings/progress UI;
- loading the preview session;
- managing the interactive preview;
- validating source/output/time/FFmpeg state;
- collecting settings into the worker configuration;
- creating/cleaning temporary config and cancel files;
- starting and monitoring `QProcess`;
- parsing worker JSON progress;
- updating progress/ETA/completion UI;
- cancellation/forced termination;
- error handling and cleanup.

The actual render/encode algorithm is not duplicated there. Splitting the process-control portion into another class could make `ExportTab` shorter, but it would mostly move the same state and lifecycle code into another file rather than reduce total complexity.
