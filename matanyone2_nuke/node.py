"""Nuke node creation and internal graph management."""

from __future__ import annotations

import os


NODE_CLASS = "MatAnyone2SoftMatte"
INTERNAL_CACHE_READ = "MA2_CacheRead"
INTERNAL_COPY = "MA2_CopyAlpha"


def create_node():
    import nuke

    group = nuke.nodes.Group(name=NODE_CLASS)
    _add_knobs(group)
    _build_initial_graph(group)
    group["tile_color"].setValue(0x3B7A57FF)
    return group


def ensure_cache_graph(node, cache_pattern: str, first_frame: int, last_frame: int) -> None:
    import nuke

    node.begin()
    try:
        video_input = _find_or_create_input("Video", 0)
        cache_read = nuke.toNode(INTERNAL_CACHE_READ)
        if cache_read is None:
            cache_read = nuke.nodes.Read(name=INTERNAL_CACHE_READ)
        cache_read["file"].setValue(cache_pattern)
        cache_read["first"].setValue(first_frame)
        cache_read["last"].setValue(last_frame)
        cache_read["origfirst"].setValue(first_frame)
        cache_read["origlast"].setValue(last_frame)

        copy = nuke.toNode(INTERNAL_COPY)
        if copy is None:
            copy = nuke.nodes.Copy(name=INTERNAL_COPY)
        copy.setInput(0, video_input)
        copy.setInput(1, cache_read)
        _set_if_exists(copy, "from0", "rgba.alpha")
        _set_if_exists(copy, "to0", "rgba.alpha")

        output = _find_or_create_output()
        output.setInput(0, copy)
    finally:
        node.end()


def reset_to_input_graph(node) -> None:
    node.begin()
    try:
        video_input = _find_or_create_input("Video", 0)
        output = _find_or_create_output()
        output.setInput(0, video_input)
    finally:
        node.end()


def _add_knobs(node) -> None:
    import nuke

    if "ma2_tab" in node.knobs():
        return

    node.addKnob(nuke.Tab_Knob("ma2_tab", "MatAnyone2"))
    node.addKnob(nuke.Text_Knob("ma2_help", "", "Input 0: RGB plate/video. Input 1: first-frame mask alpha."))
    node.addKnob(nuke.File_Knob("ma2_checkpoint", "Checkpoint"))

    cache_dir = nuke.File_Knob("ma2_cache_dir", "Cache directory")
    node.addKnob(cache_dir)

    node.addKnob(nuke.Int_Knob("ma2_first_frame", "First frame"))
    node.addKnob(nuke.Int_Knob("ma2_last_frame", "Last frame"))
    node.addKnob(nuke.Int_Knob("ma2_mask_frame", "Mask frame"))

    node.addKnob(nuke.Text_Knob("ma2_processing_label", "", "Processing"))
    node.addKnob(nuke.String_Knob("ma2_device", "CUDA device"))
    node["ma2_device"].setValue("cuda:0")
    node.addKnob(nuke.Int_Knob("ma2_warmup", "Warmup frames"))
    node["ma2_warmup"].setValue(10)
    node.addKnob(nuke.Int_Knob("ma2_erode", "Mask erode"))
    node["ma2_erode"].setValue(10)
    node.addKnob(nuke.Int_Knob("ma2_dilate", "Mask dilate"))
    node["ma2_dilate"].setValue(10)
    node.addKnob(nuke.Int_Knob("ma2_max_size", "Max processing min side"))
    node["ma2_max_size"].setValue(-1)

    run = nuke.PyScript_Knob("ma2_run", "Run MatAnyone2")
    run.setCommand("import matanyone2_nuke; matanyone2_nuke.run_node(nuke.thisNode())")
    node.addKnob(run)

    clear = nuke.PyScript_Knob("ma2_clear", "Clear Cache")
    clear.setCommand("import matanyone2_nuke; matanyone2_nuke.clear_cache(nuke.thisNode())")
    node.addKnob(clear)

    status = nuke.Text_Knob("ma2_status", "Status", "Not run")
    node.addKnob(status)

    root = nuke.root()
    node["ma2_first_frame"].setValue(int(root.firstFrame()))
    node["ma2_last_frame"].setValue(int(root.lastFrame()))
    node["ma2_mask_frame"].setValue(int(root.firstFrame()))


def _build_initial_graph(node) -> None:
    import nuke

    node.begin()
    try:
        video = _find_or_create_input("Video", 0)
        _find_or_create_input("FirstFrameMask", 1)
        output = _find_or_create_output()
        output.setInput(0, video)
    finally:
        node.end()


def _find_or_create_input(name: str, number: int):
    import nuke

    existing = nuke.toNode(name)
    if existing is not None:
        return existing
    try:
        return nuke.nodes.Input(name=name, number=number)
    except TypeError:
        node = nuke.nodes.Input(name=name)
        _set_if_exists(node, "number", number)
        return node


def _find_or_create_output():
    import nuke

    existing = nuke.toNode("Output")
    if existing is not None:
        return existing
    return nuke.nodes.Output(name="Output")


def _set_if_exists(node, knob_name: str, value) -> None:
    if knob_name in node.knobs():
        node[knob_name].setValue(value)


def nuke_pattern(path: str) -> str:
    return path.replace("\\", "/")


def default_cache_dir(node) -> str:
    import nuke

    script = nuke.root().name()
    script_name = os.path.splitext(os.path.basename(script))[0] if script else "untitled"
    node_name = node.fullName().replace(".", "_").replace(" ", "_")
    base = os.path.join(os.path.expanduser("~"), ".nuke", "matanyone2_nuke_cache")
    return os.path.join(base, script_name, node_name)
