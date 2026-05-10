"""Small EXR alpha writer used by the MatAnyone2 cache."""

from __future__ import annotations

import os
from typing import Any

import numpy as np


def write_alpha_half_exr(path: str, alpha: np.ndarray) -> None:
    """Write an RGBA half-float EXR with alpha populated and RGB black."""

    os.makedirs(os.path.dirname(path), exist_ok=True)
    alpha = np.asarray(alpha, dtype=np.float32)
    alpha = np.clip(alpha, 0.0, 1.0)

    try:
        _write_openexr(path, alpha)
        return
    except Exception as openexr_error:
        try:
            _write_cv2(path, alpha)
            return
        except Exception as cv2_error:
            raise RuntimeError(
                "Could not write EXR alpha cache. Install the OpenEXR Python package "
                "in the MatAnyone2 Nuke vendor folder."
            ) from cv2_error


def _write_openexr(path: str, alpha: np.ndarray) -> None:
    import Imath
    import OpenEXR

    height, width = alpha.shape
    header: dict[str, Any] = OpenEXR.Header(width, height)
    half = Imath.PixelType(Imath.PixelType.HALF)
    header["channels"] = {
        "R": Imath.Channel(half),
        "G": Imath.Channel(half),
        "B": Imath.Channel(half),
        "A": Imath.Channel(half),
    }

    zero = np.zeros_like(alpha, dtype=np.float16).tobytes()
    a = alpha.astype(np.float16).tobytes()

    exr = OpenEXR.OutputFile(path, header)
    try:
        exr.writePixels({"R": zero, "G": zero, "B": zero, "A": a})
    finally:
        exr.close()


def _write_cv2(path: str, alpha: np.ndarray) -> None:
    os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")

    import cv2

    bgra = np.zeros((alpha.shape[0], alpha.shape[1], 4), dtype=np.float32)
    bgra[:, :, 3] = alpha
    if not cv2.imwrite(path, bgra):
        raise RuntimeError(f"OpenCV failed to write EXR: {path}")

