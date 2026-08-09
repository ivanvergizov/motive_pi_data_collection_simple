from __future__ import annotations

import numpy as np


def create_body_vertices(length: float, width: float, height: float) -> np.ndarray:
    nose_x, base_x = length / 2.0, -length / 2.0
    half_width, half_height = width / 2.0, height / 2.0
    return np.asarray([
        [nose_x, 0.0, 0.0],
        [base_x, -half_width, -half_height],
        [base_x, half_width, -half_height],
        [base_x, 0.0, half_height],
    ], dtype=float)


def create_body_faces() -> np.ndarray:
    return np.asarray([[0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 2, 3]], dtype=int)
