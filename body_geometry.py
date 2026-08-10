from __future__ import annotations

import numpy as np

from app_types import BodyType


def create_body_geometry(
    body_type: BodyType,
    length: float,
    width: float,
    height: float,
) -> tuple[np.ndarray, np.ndarray]:
    if body_type == "tetrahedron":
        nose_x, base_x = length / 2.0, -length / 2.0
        half_width, half_height = width / 2.0, height / 2.0
        vertices = [
            [nose_x, 0.0, 0.0],
            [base_x, -half_width, -half_height],
            [base_x, half_width, -half_height],
            [base_x, 0.0, half_height],
        ]
        faces = [[0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 2, 3]]
    elif body_type == "rectangular_prism":
        x, y, z = length / 2.0, width / 2.0, height / 2.0
        vertices = [
            [-x, -y, -z], [x, -y, -z], [x, y, -z], [-x, y, -z],
            [-x, -y, z], [x, -y, z], [x, y, z], [-x, y, z],
        ]
        faces = [
            [0, 2, 1], [0, 3, 2],
            [4, 5, 6], [4, 6, 7],
            [0, 1, 5], [0, 5, 4],
            [1, 2, 6], [1, 6, 5],
            [2, 3, 7], [2, 7, 6],
            [3, 0, 4], [3, 4, 7],
        ]
    else:
        raise ValueError(f"Unknown rigid-body type: {body_type!r}")

    return np.asarray(vertices, dtype=float), np.asarray(faces, dtype=int)
