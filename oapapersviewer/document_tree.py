# -*- coding: UTF-8 -*-
""""
Created on 01.08.22
Module with document tree widget.

:author:     Martin Dočekal
"""
from dataclasses import dataclass, asdict
from functools import lru_cache
from typing import Dict, Union, NewType, List, Optional, Callable, Any

from oapapersloader.bib_entry import BibEntry
from oapapersloader.datasets import OADataset
from oapapersloader.document import Document
from oapapersloader.hierarchy import Hierarchy, TextContent, RefSpan
from rich.console import RenderableType
from rich.text import Text
from textual import events
from textual.widgets import TreeControl, NodeID, TreeNode, TreeClick


class HierarchyTree(TreeControl[Hierarchy]):
    """
    Makes tree widget from hierarchy.
    """

    def __init__(self, h: Hierarchy) -> None:
        """
        initialization of hierarchy TREE

        :param h: hierarchy that should be shown
        """

        super().__init__("", data=h)
        self.root.tree.guide_style = "white"
        self._tree.hide_root = True


@dataclass
class Citation:
    document: Union[int, Document]  # int when the document is not loaded


@dataclass
class CitationSpan:
    ref: RefSpan
    text_content: TextContent


DocumentTreeNodeData = NewType("DocumentTreeNodeData", Union[None, int, str, Hierarchy, Document, TextContent, List,
                                                             Dict, RefSpan, Citation, BibEntry])
"""
@dataclass
class DocumentTreeNodeData:
    data: Union[None, int, str, Hierarchy, Document]
    expandable: bool
"""


class DocumentTree(TreeControl[DocumentTreeNodeData]):
    """
    Makes tree widget from document.
    """

    def __init__(self, d: Document, resolve_citations: Optional[OADataset] = None,
                 show_reference_callback: Optional[Callable[[Document], Any]] = None) -> None:
        """
        initialization of document TREE

        :param d: document that should be shown
        :param resolve_citations: If not none than the resolving of citation will be activated. Do not forget to pass
            also show_reference_callback.
        :param show_reference_callback: Callback that will be called with appropriate reference document that
            should be shown. Do not forget to pass also resolve_citations dataset.
        """
        assert (resolve_citations is None and show_reference_callback is None) or \
               (resolve_citations is not None and show_reference_callback is not None)

        super().__init__("", data=d)
        self.root.tree.guide_style = "white"
        self._tree.hide_root = True
        self.resolve_citations = resolve_citations
        self.show_reference_callback = show_reference_callback
        self.hint_text_color = "#999999"

    async def watch_hover_node(self, hover_node: NodeID) -> None:
        for node in self.nodes.values():
            node.tree.guide_style = (
                "bold not dim red" if node.id == hover_node else "white"
            )
        self.refresh(layout=True)

    def render_node(self, node: TreeNode[Document]) -> RenderableType:
        return self.render_tree_label(
            node,
            self.is_expandable(node),
            node.expanded,
            node.id == self.hover_node,
        )

    @staticmethod
    def is_expandable(node: TreeNode[Document]) -> bool:
        """
        checks whether given node is expandable

        :param node: the node to check
        """
        if isinstance(node.data, dict) or isinstance(node.data, list) or isinstance(node.data, Hierarchy) or \
                isinstance(node.data, TextContent) or isinstance(node.data, RefSpan) or \
                isinstance(node.data, Document) or isinstance(node.data, CitationSpan) or \
                isinstance(node.data, BibEntry):
            # type match
            if isinstance(node.data, dict) or isinstance(node.data, list):
                return len(node.data) > 0
            return True
        return False

    @lru_cache(maxsize=1024 * 32)
    def render_tree_label(
            self,
            node: TreeNode[Document],
            is_expandable: bool,
            expanded: bool,
            is_hover: bool,
    ) -> RenderableType:
        meta = {
            "@click": f"click_label({node.id})",
            "tree_node": node.id,
            "cursor": node.is_cursor,
        }

        if node.label == "" and not self.is_expandable(node):
            icon_label = Text("")
        else:
            if node.label is None:
                label = Text("None")
            else:
                label = Text(f'"{node.label}"')

            label.stylize("bold magenta")
            if is_hover:
                label.stylize("underline")
            icon = ""
            if is_expandable:
                icon = "⊟" if expanded else "⊞"

            icon_label = label + Text(f": {icon}", overflow="ellipsis")
            icon_label.apply_meta(meta)

            if self.resolve_citations and (isinstance(node.data, CitationSpan) or isinstance(node.data, BibEntry)):
                if isinstance(node.data, CitationSpan):
                    cite_id = self.data.bibliography[node.data.ref.index].id if node.data.ref.index is not None \
                        else None
                else:
                    cite_id = node.data.id

                if cite_id is not None:
                    try:
                        view_label_part = Text(f" (👁  {self.resolve_citations.get_by_id(cite_id).title})",
                                               style=self.hint_text_color)
                        view_label_part.apply_meta({
                            "@click": f"show_reference({cite_id})",
                            "tree_node": node.id,
                            "cursor": node.is_cursor,
                        })
                    except KeyError:
                        view_label_part = Text(f" (not in references)", style=self.hint_text_color)

                    icon_label += view_label_part

        if is_expandable:
            return icon_label
        else:

            if isinstance(node.data, Citation):
                if isinstance(node.data.document, int):
                    data = Text(str(node.data.document))
                else:
                    data = Text(str(node.data.document.id) + " 👁 ")
                    data.append(Text(" | " + node.data.document.title, style=self.hint_text_color))
                    icon_label.apply_meta({
                        "@click": f"show_reference({node.data.document.id})",
                        "tree_node": node.id,
                        "cursor": node.is_cursor,
                    })
                    data.apply_meta({
                        "@click": f"show_reference({node.data.document.id})",
                        "tree_node": node.id,
                        "cursor": node.is_cursor,
                    })

                    if is_hover:
                        data.stylize("underline")
            else:
                data = Text(str(node.data))
            return icon_label + data

    async def on_mount(self, event: events.Mount) -> None:
        await self.create_sub_nodes(self.root)
        await self.call_later(self.root.expand)

    async def create_sub_nodes(self, node: TreeNode[DocumentTreeNodeData]):
        if isinstance(node.data, Document):
            await node.add("id", node.data.id)
            await node.add("s2orc_id", node.data.s2orc_id)
            await node.add("mag_id", node.data.mag_id)

            doi_data = None
            if node.data.doi is not None:
                doi_data = node.data.doi if node.data.doi.startswith("http") \
                    else f"https://doi.org/{node.data.doi.strip('/')}"

            await node.add("doi", doi_data)
            await node.add("title", node.data.title)

            await node.add("authors", node.data.authors)
            await self.create_sub_nodes(node.children[-1])
            await self.call_later(node.children[-1].expand)

            await node.add("year", node.data.year)

            await node.add("fields of study", node.data.fields_of_study)
            await self.create_sub_nodes(node.children[-1])
            await self.call_later(node.children[-1].expand)

            if self.resolve_citations is None:
                citations = node.data.citations
            else:
                citations = [Citation(self.resolve_citations.get_by_id(c) if c in self.resolve_citations else c) for c in node.data.citations]

            await node.add("citations", citations)
            await self.create_sub_nodes(node.children[-1])
            await self.call_later(node.children[-1].expand)

            if hasattr(node.data, "related_work"):
                await node.add("related work hierarchy", node.data.related_work)
                await self.create_sub_nodes(node.children[-1])
                await self.call_later(node.children[-1].expand)

                await node.add("related work in hierarchy position", node.data.related_work_orig_path)

            await node.add("hierarchy", node.data.hierarchy)
            await self.create_sub_nodes(node.children[-1])
            await self.call_later(node.children[-1].expand)

            await node.add("bibliography", node.data.bibliography)
            await self.create_sub_nodes(node.children[-1])
            await self.call_later(node.children[-1].expand)

            await node.add("non plaintext content", node.data.non_plaintext_content)

        elif isinstance(node.data, Hierarchy):
            await node.add(node.data.headline, node.data.content)
            if node.data.headline and len(list(node.data.sections())) > 0:  # only for those containing another section
                await self.create_sub_nodes(node.children[-1])
                await self.call_later(node.children[-1].expand)

        elif isinstance(node.data, TextContent):
            await node.add("text", node.data.text)
            await node.add("citations", [CitationSpan(c, node.data) for c in node.data.citations])
            await node.add("references", node.data.references)

        elif isinstance(node.data, BibEntry):
            await node.add("id", node.data.id)
            await node.add("title", node.data.title)
            await node.add("year", node.data.year)
            await node.add("authors", list(node.data.authors))

        elif isinstance(node.data, RefSpan):
            await node.add("index", node.data.index)
            await node.add("start", node.data.start)
            await node.add("end", node.data.end)

        elif isinstance(node.data, CitationSpan):
            await node.add("index", node.data.ref.index)
            await node.add("start", node.data.ref.start)
            await node.add("end", node.data.ref.end)
            bib_entry = {}
            if node.data.ref.index is not None:
                bib_entry = self.data.bibliography[node.data.ref.index]
                bib_entry.authors = list(bib_entry.authors)  # the tuple was showing in single line
                bib_entry = asdict(bib_entry)

            # asdict is here because we do not want to show bib entry link again (it is shown for every citation span)
            await node.add("bib_entry", bib_entry)
            await node.add("span", node.data.text_content.text[node.data.ref.start:node.data.ref.end])

        elif isinstance(node.data, list):
            for i, x in enumerate(node.data):
                if isinstance(x, Hierarchy):
                    await node.add(x.headline, x.content)
                    if x.headline and len(list(x.sections())) > 0:  # only for those containing another section
                        await self.create_sub_nodes(node.children[-1])
                        await self.call_later(node.children[-1].expand)
                elif isinstance(x, CitationSpan):
                    await node.add(str(x.ref.index), x)
                elif isinstance(x, BibEntry):
                    await node.add(str(i), x)
                else:
                    await node.add("", x)

        elif isinstance(node.data, dict):
            for k, v in node.data.items():
                await node.add(k, v)

        node.loaded = True

    async def handle_tree_click(self, message: TreeClick[Document]) -> None:
        if not message.node.loaded and self.is_expandable(message.node):
            await self.create_sub_nodes(message.node)
            await message.node.expand()
        else:
            await message.node.toggle()

    async def action_show_reference(self, document_id: int):
        """
        Calls callback for showing reference.

        :param document_id: id of document that should be shown
        """
        await self.show_reference_callback(self.resolve_citations.get_by_id(document_id))
