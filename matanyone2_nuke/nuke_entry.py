"""Nuke-facing run, export, and cache management functions."""

from __future__ import annotations

import os
import shutil
from contextlib import contextmanager

from .node import default_cache_dir, ensure_cache_graph, nuke_pattern, reset_to_input_graph
from .runner import RunSettings, run_sequence


def run_selected() -> None:
    import nuke

    run_node(nuke.selectedNode())


def run_node(node=None) -> None:
    import nuke

    if node is None:
        node = nuke.thisNode()

    _require_nuke_15_python()
    _require_inputs(node)

    first = int(node["ma2_first_frame"].value())
    last = int(node["ma2_last_frame"].value())
    mask_frame = int(node["ma2_mask_frame"].value())
    if last < first:
        raise ValueError("Last frame must be greater than or equal to first frame.")

    cache_dir = node["ma2_cache_dir"].value().strip() or default_cache_dir(node)
    cache_dir = os.path.abspath(os.path.expanduser(cache_dir))
    export_dir = os.path.join(cache_dir, "_export")
    matte_dir = os.path.join(cache_dir, "matte")
    os.makedirs(export_dir, exist_ok=True)
    os.makedirs(matte_dir, exist_ok=True)

    _set_status(node, "Exporting frames from Nuke")
    with _temp_write_node(node.input(0), os.path.join(export_dir, "src.%05d.png"), "rgb") as write:
        nuke.execute(write.name(), first, last)

    mask_path = os.path.join(export_dir, f"mask.{mask_frame:05d}.png")
    with _temp_write_node(node.input(1), mask_path, "rgba") as write:
        nuke.execute(write.name(), mask_frame, mask_frame)

    output_pattern = os.path.join(matte_dir, "matte.%05d.exr")
    frame_numbers = list(range(first, last + 1))

    settings = RunSettings(
        frames_dir=export_dir,
        frame_numbers=frame_numbers,
        frame_pattern=os.path.join(export_dir, "src.%05d.png"),
        mask_path=mask_path,
        output_dir=matte_dir,
        output_pattern=output_pattern,
        checkpoint_path=node["ma2_checkpoint"].value().strip(),
        device=node["ma2_device"].value().strip() or "cuda:0",
        warmup=int(node["ma2_warmup"].value()),
        erode=int(node["ma2_erode"].value()),
        dilate=int(node["ma2_dilate"].value()),
        max_size=int(node["ma2_max_size"].value()),
    )

    def progress(message: str) -> None:
        _set_status(node, message)
        nuke.tprint(f"[MatAnyone2] {message}")

    outputs = run_sequence(settings, progress=progress)
    if not outputs:
        raise RuntimeError("MatAnyone2 produced no cache frames.")

    ensure_cache_graph(node, nuke_pattern(output_pattern), first, last)
    node["ma2_cache_dir"].setValue(cache_dir)
    _set_status(node, f"Done: {len(outputs)} EXR matte frames")


def clear_selected_cache() -> None:
    import nuke

    clear_cache(nuke.selectedNode())


def clear_cache(node=None) -> None:
    import nuke

    if node is None:
        node = nuke.thisNode()
    cache_dir = node["ma2_cache_dir"].value().strip() or default_cache_dir(node)
    cache_dir = os.path.abspath(os.path.expanduser(cache_dir))
    if os.path.isdir(cache_dir):
        shutil.rmtree(cache_dir)
    reset_to_input_graph(node)
    _set_status(node, "Cache cleared")


def _require_nuke_15_python() -> None:
    import sys

    if sys.version_info < (3, 10):
        raise RuntimeError(
            "MatAnyone2 requires Python 3.10+. Use Nuke 15.x or newer for direct mode."
        )


def _require_inputs(node) -> None:
    if node.input(0) is None:
        raise ValueError("Connect the RGB video/plate to input 0.")
    if node.input(1) is None:
        raise ValueError("Connect the first-frame mask alpha to input 1.")


def _set_status(node, message: str) -> None:
    if "ma2_status" in node.knobs():
        node["ma2_status"].setValue(message)


@contextmanager
def _temp_write_node(input_node, file_path: str, channels: str):
    import nuke

    write = nuke.nodes.Write(file=nuke_pattern(file_path), file_type="png")
    write.setInput(0, input_node)
    if "channels" in write.knobs():
        write["channels"].setValue(channels)
    if "raw" in write.knobs():
        write["raw"].setValue(True)
    try:
        yield write
    finally:
        nuke.delete(write)
