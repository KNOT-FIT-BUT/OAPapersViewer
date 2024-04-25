# -*- coding: UTF-8 -*-
""""
Created on 01.08.22
Module with JSON tree widget.

:author:     Martin Dočekal
"""
from oapapersloader.myjson import json_loads
from functools import lru_cache

from rich.console import RenderableType
from rich.text import Text
from textual import events
from textual.reactive import Reactive
from textual.widgets import TreeControl, NodeID, TreeNode, TreeClick
from typing import Dict, Union, Sequence, NewType, List

JSONTreeNodeDataType = NewType("JSONTreeNodeDataType", Union[Dict, List])


class JSONTree(TreeControl[JSONTreeNodeDataType]):
    """
    Makes tree widget from json.
    """
    has_focus: Reactive[bool] = Reactive(False)

    def __init__(self, data: Union[str, Dict, Sequence], label: str = "") -> None:
        """
        initialization of json TREE

        :param data: you can pass json string or directory/list of items
        :param label: label of this tree node
        """

        if isinstance(data, str):
            data = json_loads(data)
        super().__init__(label, data=data)
        self.root.tree.guide_style = "white"

    def on_focus(self) -> None:
        self.has_focus = True

    def on_blur(self) -> None:
        self.has_focus = False

    async def watch_hover_node(self, hover_node: NodeID) -> None:
        for node in self.nodes.values():
            node.tree.guide_style = (
                "bold not dim red" if node.id == hover_node else "black"
            )
        self.refresh(layout=True)

    def render_node(self, node: TreeNode[JSONTreeNodeDataType]) -> RenderableType:
        return self.render_tree_label(
            node,
            self.is_expandable(node),
            node.expanded,
            node.is_cursor,
            node.id == self.hover_node,
            self.has_focus,
        )

    @staticmethod
    def is_expandable(node: TreeNode[JSONTreeNodeDataType]) -> bool:
        """
        checks whether given node is expandable

        :param node: the node to check
        """

        return isinstance(node.data, dict) or isinstance(node.data, list)

    @lru_cache(maxsize=1024 * 32)
    def render_tree_label(
        self,
        node: TreeNode[JSONTreeNodeDataType],
        is_expandable: bool,
        expanded: bool,
        is_cursor: bool,
        is_hover: bool,
        has_focus: bool,
    ) -> RenderableType:
        meta = {
            "@click": f"click_label({node.id})",
            "tree_node": node.id,
            "cursor": node.is_cursor,
        }

        if node.label == "" and not self.is_expandable(node):
            icon_label = Text("")
        else:
            label = Text('"'+node.label+'"') if isinstance(node.label, str) else node.label
            if is_hover:
                label.stylize("underline")
            icon = ""
            if is_expandable:
                label.stylize("bold magenta")
                icon = "⊟" if expanded else "⊞"

            if is_cursor and has_focus:
                label.stylize("reverse")

            icon_label = label + Text(f": {icon}", no_wrap=True, overflow="ellipsis")
            icon_label.apply_meta(meta)

        if is_expandable:
            return icon_label
        else:
            return icon_label + Text(str(node.data), no_wrap=True)

    async def on_mount(self, event: events.Mount) -> None:
        await self.create_sub_nodes(self.root)

    async def create_sub_nodes(self, node: TreeNode[JSONTreeNodeDataType]):
        if isinstance(node.data, dict):
            for k, v in node.data.items():
                await node.add(k, v)
        elif isinstance(node.data, list):
            for entry in node.data:
                await node.add("", entry)

        node.loaded = True
        await node.expand()
        self.refresh(layout=True)

    async def handle_tree_click(self, message: TreeClick[JSONTreeNodeDataType]) -> None:
        if not message.node.loaded and self.is_expandable(message.node):
            await self.create_sub_nodes(message.node)
            await message.node.expand()
        else:
            await message.node.toggle()
