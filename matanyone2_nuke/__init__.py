"""Public entrypoints used by Nuke knobs and menus."""

from __future__ import annotations


__version__ = "0.1.0"


def run_selected() -> None:
    from .nuke_entry import run_selected

    run_selected()


def run_node(node=None) -> None:
    from .nuke_entry import run_node

    run_node(node)


def clear_selected_cache() -> None:
    from .nuke_entry import clear_selected_cache

    clear_selected_cache()


def clear_cache(node=None) -> None:
    from .nuke_entry import clear_cache

    clear_cache(node)

