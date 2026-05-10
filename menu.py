"""Nuke menu entry for MatAnyone2 for Nuke."""

from __future__ import annotations

import nuke


def _create_node() -> None:
    from matanyone2_nuke.node import create_node

    create_node()


nuke.menu("Nodes").addCommand(
    "Keyer/MatAnyone2 Soft Matte",
    _create_node,
    icon="Keyer.png",
)

