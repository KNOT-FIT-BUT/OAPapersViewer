# -*- coding: UTF-8 -*-
""""
Created on 01.08.22

Contains view for listing samples in a dataset.

:author:     Martin Dočekal
"""
import enum
import math
from typing import Optional

from rich import box
from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.traceback import Traceback
from textual import events, log
from textual.binding import Bindings
from textual.widgets import ScrollView

from oapapersloader.datasets import OADataset
from oapapersviewer.bindings_dock_view import BindingsDockView
from oapapersviewer.footer import FooterView, PromptFormat
from oapapersviewer.inputs import IntegerInput


class State(enum.Enum):
    """
    all app states
    """
    LISTING = enum.auto()
    PROMPTING_ID = enum.auto()
    PROMPTING_INDEX = enum.auto()
    PROMPTING_PAGE = enum.auto()


class ListingView(BindingsDockView):
    """
    Shows listing view os dataset samples.
    """

    def __init__(self, dataset: OADataset, items_per_page: int = 100, name: Optional[str] = None):
        """
        initialization of listing

        :param dataset: dataset that should be listed
        :param items_per_page:  maximal number of samples per single page
        :param name:  name of this view
        """
        super().__init__(name)
        self.dataset = dataset
        self.page = 0
        self.items_per_page = items_per_page
        self.body = None
        self.footer = None
        self.row_selector = -1
        self.table = None
        self.state = State.LISTING

    @staticmethod
    def create_bindings(action_prefix: str = "") -> Bindings:
        """
        Creates new bindings object that contains necessary bindings to use this view.

        :param action_prefix: prefix for action naming
        """
        bindings = Bindings()
        bindings.bind("up", action_prefix+"move_row_selector(-1)", "Row selector up", allow_forward=False)
        bindings.bind("down", action_prefix+"move_row_selector(1)", "Row selector down", allow_forward=False)
        bindings.bind("left", action_prefix+"previous_page", "Previous page")
        bindings.bind("right", action_prefix+"next_page", "Next page")
        bindings.bind("v", action_prefix+"go_view_id", "View document with id")
        bindings.bind("i", action_prefix+"go_to_index", "Go to index")
        bindings.bind("p", action_prefix+"go_to_page", "Go to page")
        bindings.bind("enter", action_prefix+"manage_enter", show=False)

        return bindings

    async def on_mount(self, event: events.Mount) -> None:
        self.body = ScrollView(auto_width=True)
        self.footer = FooterView()

        await self.dock(self.footer, edge="bottom")
        await self.footer.hints()
        await self.dock(self.body)

        await self.show_page()

    async def on_resize(self, event: events.Resize) -> None:
        self.table.width = Console().width - 1
        await super().on_resize(event)

    @property
    def max_page(self) -> int:
        """
        Returns max page starting from zero, so for showing user use +1.
        """
        return math.ceil(len(self.dataset) / self.items_per_page) - 1

    async def show_page(self):
        """
        Shows given page.
        """
        try:
            self.table = table = Table(
                title=f"{self.dataset.path_to} | page {self.page + 1}/{self.max_page + 1} | "
                      f"size {len(self.dataset)}",
                width=Console().width - 1, box=box.ROUNDED)

            table.add_column("Ind.")
            table.add_column("ID")
            table.add_column("Title", ratio=3, overflow="ellipsis", no_wrap=True)
            table.add_column("Authors", ratio=1, overflow="ellipsis", no_wrap=True)
            table.add_column("Year")
            table.add_column("Cit.", justify="center")

            page_offset = self.page * self.items_per_page
            for i, document in enumerate(self.dataset[page_offset: page_offset + self.items_per_page]):
                authors = ", ".join(document.authors)

                if self.row_selector == i:
                    style = Style(color="black", bgcolor="white", meta={
                        "@click": f"body.row_mouse_selector({i})",
                    })
                else:
                    style = Style(meta={
                        "@click": f"body.row_mouse_selector({i})",
                    })

                table.add_row(f"{page_offset + i}", f"{document.id}", f"{document.title}", f"{authors}",
                              f"{document.year}", f"{len(document.citations)}", style=style)

        except Exception:
            table = Traceback(theme="monokai", width=None, show_locals=True)

        await self.body.update(table, home=False)

    async def action_previous_page(self):
        await self.change_page(self.page - 1)

    async def action_next_page(self):
        await self.change_page(self.page + 1)

    async def action_go_to_page(self):
        self.state = State.PROMPTING_PAGE
        await self.footer.prompting("Enter page number", PromptFormat.INTEGER)

    async def action_go_view_id(self):
        self.state = State.PROMPTING_ID
        await self.footer.prompting("Enter id", PromptFormat.INTEGER)

    async def action_go_to_index(self):
        self.state = State.PROMPTING_INDEX
        await self.footer.prompting("Enter index", PromptFormat.INTEGER)

    async def change_page(self, page: int):
        """
        changes page

        :param page: the page we want to see
        """
        new_page = max(0, min(self.max_page, page))

        if self.page != new_page:
            self.page = new_page
            self.row_selector = -1
            await self.show_page()

    async def change_index(self, index: int):
        """
        changes active sample to one with given index

        :param index: the index of a sample
        """
        index = max(0, min(len(self.dataset)-1, index))
        page = index // self.items_per_page
        await self.change_page(page)
        await self.change_row_selector(index - (self.items_per_page * page))

    async def action_manage_enter(self):
        if self.state == State.PROMPTING_PAGE:
            prompt: IntegerInput = self.footer.prompt
            await self.footer.hints()
            self.state = self.state.LISTING
            await self.change_page(prompt.value - 1)
        elif self.state == State.PROMPTING_INDEX:
            prompt: IntegerInput = self.footer.prompt
            await self.footer.hints()
            self.state = self.state.LISTING
            await self.change_index(prompt.value)
        elif self.state == State.PROMPTING_ID:
            prompt: IntegerInput = self.footer.prompt
            await self.footer.hints()

            try:
                await self.app.show(self.dataset.get_by_id(prompt.value))
            except KeyError:
                await self.app.action_bell()
            prompt.value = None
            self.state = State.LISTING

        elif self.state == State.LISTING and self.row_selector >= 0:
            await self.app.show(self.dataset[self.page*self.items_per_page + self.row_selector])

    async def action_move_row_selector(self, shift: int):
        """
        Moves with row selector.

        :param shift: how much the selector should be shifted
        """
        await self.change_row_selector(self.row_selector + shift)

    async def action_row_mouse_selector(self, row_index: int):
        """
        Changes selected row in table. If the new row_index is the same as row_index before it will open the document
        instead.
        this action was created for mouse click

        :param row_index: new row index
            -1 clears the selector
        """
        log(f"CALLED action_row_mouse_selector with {row_index}")
        if self.row_selector == row_index:
            await self.app.show(self.dataset[self.page * self.items_per_page + self.row_selector])
        else:
            await self.change_row_selector(row_index)

    async def change_row_selector(self, row_index: int):
        """
        changes row selector to different row index

        :param row_index: new row index
            -1 clears the selector
        """
        if self.row_selector > -1:
            self.table.rows[self.row_selector].style = Style(meta={
                        "@click": f"body.row_mouse_selector({self.row_selector})",
                    })
        self.row_selector = max(-1, min(min(len(self.dataset), self.items_per_page) - 1, row_index))
        if self.row_selector > -1:
            self.table.rows[self.row_selector].style = Style(color="black", bgcolor="white", meta={
                        "@click": f"body.row_mouse_selector({self.row_selector})",
                    })

        self.body: ScrollView
        await self.body.update(self.table, home=False)

        # check whether we are still in view
        view_line = self.row_selector + 4 # + 4 because of title and header
        if not(self.body.y <= view_line < self.body.y + self.body.size.height):
            # not in view
            self.body.scroll_in_to_view(self.row_selector + 4)

