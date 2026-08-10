from __future__ import annotations

import numpy as np
import pyvista as pv
from vtkmodules.vtkRenderingCore import vtkBillboardTextActor3D

from app_types import BodyDisplaySettings, RoomBounds, SceneFrame
from body_geometry import create_body_geometry
from constants import (
    PYVISTA_AXIS_COLOR,
    PYVISTA_AXIS_FONT_SIZE,
    PYVISTA_BODY_LABEL_FONT_SIZE,
    PYVISTA_BODY_LABEL_OFFSET,
    PYVISTA_GRID_COLOR,
)
from rigid_body_math import quaternion_xyzw_to_rotation_matrix


def _add_body_label(target, name: str) -> vtkBillboardTextActor3D:
    label = vtkBillboardTextActor3D()
    label.SetInput(name)
    label.SetDisplayOffset(0, PYVISTA_BODY_LABEL_OFFSET)
    label.SetVisibility(False)
    text = label.GetTextProperty()
    text.SetColor(0.08, 0.08, 0.08)
    text.SetFontSize(PYVISTA_BODY_LABEL_FONT_SIZE)
    text.SetJustificationToCentered()
    text.SetVerticalJustificationToBottom()
    target.add_actor(label, reset_camera=False, name=f"label:{name}", pickable=False, render=False)
    return label


def add_body_labels(
    target,
    settings: dict[str, BodyDisplaySettings],
) -> dict[str, vtkBillboardTextActor3D]:
    return {name: _add_body_label(target, name) for name in settings}


def add_body_actors(
    plotter,
    settings: dict[str, BodyDisplaySettings],
    line_scale: float = 1.0,
) -> dict[str, pv.Actor]:
    actors: dict[str, pv.Actor] = {}

    for name, setting in settings.items():
        vertices, faces = create_body_geometry(
            setting.body_type, setting.length, setting.width, setting.height
        )
        vtk_faces = np.column_stack([np.full(len(faces), 3, dtype=np.int64), faces]).reshape(-1)
        mesh = pv.PolyData(np.asarray(vertices, dtype=float), vtk_faces)

        actor = plotter.add_mesh(
            mesh,
            color=setting.color,
            opacity=0.6,
            show_edges=True,
            edge_color="#262626",
            line_width=line_scale,
            smooth_shading=False,
            reset_camera=False,
            render=False,
            name=f"body:{name}",
        )
        actor.visibility = False
        actor.use_bounds = False
        actors[name] = actor

    return actors


def add_room_bounds(plotter, bounds: RoomBounds, line_scale: float = 1.0):
    x_span, y_span, z_span = bounds.spans()
    actor = plotter.show_bounds(
        bounds=list(bounds.as_sequence()),
        grid="back",
        location="outer",
        ticks="both",
        all_edges=True,
        xtitle="X (m)",
        ytitle="Y (m)",
        ztitle="Z (m)",
        n_xlabels=max(2, round(x_span / bounds.x_tick) + 1),
        n_ylabels=max(2, round(y_span / bounds.y_tick) + 1),
        n_zlabels=max(2, round(z_span / bounds.z_tick) + 1),
        color="#4c4c4c",
        bold=False,
        font_size=PYVISTA_AXIS_FONT_SIZE,
        use_3d_text=False,
        render=False,
    )

    for getter in (
        actor.GetXAxesLinesProperty,
        actor.GetYAxesLinesProperty,
        actor.GetZAxesLinesProperty,
    ):
        prop = getter()
        prop.SetColor(*PYVISTA_AXIS_COLOR)
        prop.SetLineWidth(1.5 * line_scale)

    for getter in (
        actor.GetXAxesGridlinesProperty,
        actor.GetYAxesGridlinesProperty,
        actor.GetZAxesGridlinesProperty,
    ):
        prop = getter()
        prop.SetColor(*PYVISTA_GRID_COLOR)
        prop.SetOpacity(0.55)
        prop.SetLineWidth(line_scale)

    return actor


def set_room_components(actor, *, axes: bool, grid: bool, text: bool) -> None:
    for getter in (
        actor.GetXAxesLinesProperty,
        actor.GetYAxesLinesProperty,
        actor.GetZAxesLinesProperty,
    ):
        getter().SetOpacity(1.0 if axes else 0.0)

    for getter in (
        actor.GetXAxesGridlinesProperty,
        actor.GetYAxesGridlinesProperty,
        actor.GetZAxesGridlinesProperty,
    ):
        getter().SetOpacity(0.55 if grid else 0.0)

    for getter in (
        actor.GetXAxesTitleProperty,
        actor.GetYAxesTitleProperty,
        actor.GetZAxesTitleProperty,
        actor.GetXAxesLabelProperty,
        actor.GetYAxesLabelProperty,
        actor.GetZAxesLabelProperty,
    ):
        getter().SetOpacity(1.0 if text else 0.0)

    if not axes:
        actor.XAxisTickVisibilityOff()
        actor.YAxisTickVisibilityOff()
        actor.ZAxisTickVisibilityOff()
        actor.XAxisMinorTickVisibilityOff()
        actor.YAxisMinorTickVisibilityOff()
        actor.ZAxisMinorTickVisibilityOff()


def update_body_actors(actors, frame: SceneFrame | None) -> None:
    for name, actor in actors.items():
        pose = None if frame is None else frame.poses.get(name)
        if pose is None:
            actor.visibility = False
            continue

        transform = np.eye(4, dtype=float)
        transform[:3, :3] = quaternion_xyzw_to_rotation_matrix(*map(float, pose.quaternion_xyzw))
        transform[:3, 3] = np.asarray(pose.position, dtype=float)
        actor.user_matrix = transform
        actor.visibility = True


def update_body_labels(
    labels,
    settings: dict[str, BodyDisplaySettings],
    frame: SceneFrame | None,
) -> None:
    for name, label in labels.items():
        pose = None if frame is None else frame.poses.get(name)
        if pose is None:
            label.SetVisibility(False)
            continue

        label_position = np.asarray(pose.position, dtype=float).copy()
        label_position[2] += max(settings[name].max_dimension * 0.75, 0.03)
        label.SetPosition(*map(float, label_position))
        label.SetVisibility(True)


def frame_camera(plotter, bounds: RoomBounds) -> None:
    cx, cy, cz = bounds.center()
    x_span, y_span, z_span = bounds.spans()
    diagonal = max((x_span * x_span + y_span * y_span + z_span * z_span) ** 0.5, 1.0)
    plotter.camera.focal_point = (cx, cy, cz)
    plotter.camera.position = (cx + diagonal, cy + diagonal, cz + diagonal * 0.65)
    plotter.camera.up = (0.0, 0.0, 1.0)
    plotter.camera.reset_clipping_range()


def camera_state(plotter) -> dict:
    camera = plotter.camera
    return {
        "position": list(map(float, camera.position)),
        "focal_point": list(map(float, camera.focal_point)),
        "up": list(map(float, camera.up)),
        "view_angle": float(camera.view_angle),
    }


def apply_camera_state(plotter, state: dict) -> None:
    plotter.camera.position = tuple(state["position"])
    plotter.camera.focal_point = tuple(state["focal_point"])
    plotter.camera.up = tuple(state["up"])
    plotter.camera.view_angle = float(state["view_angle"])
    plotter.camera.reset_clipping_range()
