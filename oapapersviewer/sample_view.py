# -*- coding: UTF-8 -*-
""""
Created on 01.08.22

Module containing view for viewing samples.

:author:     Martin Dočekal
"""
import math

from rich.console import Console
from textual import events, messages
from textual.binding import Bindings
from textual.widgets import ScrollView

from oapapersloader.datasets import OADataset
from oapapersloader.document import Document
from oapapersviewer.bindings_dock_view import BindingsDockView
from oapapersviewer.document_tree import DocumentTree
from oapapersviewer.footer import FooterView


class SampleView(BindingsDockView):
    """
    Class for viewing dataset samples.
    """

    def __init__(self, d: Document, references_dataset: OADataset, right_panel_fraction: float = 0.4):
        """
        initialization of sample view

        :param d: the document you'd like to see
        :param references_dataset: dataset containing referenced documents
        :param right_panel_fraction: size fraction of right panel size
        """
        super().__init__()
        self.document = d
        self.references_dataset = references_dataset
        self.document_view = None
        self.reference_view = None
        self.footer = None
        self.right_panel_fraction = right_panel_fraction

    async def on_resize(self, event: events.Resize) -> None:
        await super().on_resize(event)

        self.named_widgets["right_panel"].layout_size = math.floor(Console().width * self.right_panel_fraction)
        self.named_widgets["left_panel"].layout_size = (math.floor(Console().width * (1 - self.right_panel_fraction))) \
            if self.named_widgets["right_panel"].visible else Console().width

    async def on_mount(self, event: events.Mount) -> None:

        self.footer = FooterView()
        await self.dock(self.footer, edge="bottom")
        await self.footer.hints()

        self.document_view = ScrollView(auto_width=True)
        self.reference_view = ScrollView(auto_width=True)

        await self.dock(self.document_view, name="left_panel", edge="left")
        await self.dock(self.reference_view, size=math.floor(Console().width*self.right_panel_fraction),
                        name="right_panel", edge="right")
        await self.action_toggle("right_panel")

        await self.document_view.update(DocumentTree(self.document, resolve_citations=self.references_dataset,
                                                     show_reference_callback=self.show_reference))
        await self.reference_view.update("No referenced document is selected")

    async def show_reference(self, document: Document):
        """
        Shows given reference.

        :param document: the reference
        """
        await self.reference_view.update(DocumentTree(document))
        self.named_widgets["left_panel"].layout_size = math.floor(Console().width*(1-self.right_panel_fraction))
        self.named_widgets["right_panel"].visible = True
        await self.post_message(messages.Layout(self))

    @staticmethod
    def create_bindings(action_prefix: str = "") -> Bindings:
        bindings = Bindings()
        bindings.bind("h", action_prefix + "hide_right_panel", "Hide right panel")
        return bindings

    async def action_hide_right_panel(self):
        """
        Hides right panel if it is visible.
        """
        self.named_widgets["right_panel"].visible = False
        self.named_widgets["left_panel"].layout_size = math.floor(Console().width)
        await self.post_message(messages.Layout(self))


