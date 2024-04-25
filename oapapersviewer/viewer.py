# -*- coding: UTF-8 -*-
""""
Created on 28.07.22
Contains TUI viewer for OAPapers.

:author:     Martin Dočekal
"""
import enum
from typing import Type, Union, Optional

from textual import events
from textual.app import App
from textual.driver import Driver

from oapapersloader import OADataset, Document
from .listing import ListingView
from .sample_view import SampleView


class State(enum.Enum):
    """
    all app states
    """
    LISTING = enum.auto()
    VIEWING = enum.auto()


class Viewer(App):
    """
    TUI dataset viewer.
    """

    def __init__(self, dataset: OADataset, references_dataset: Optional[OADataset] = None, items_per_page: int = 100,
                 screen: bool = True, driver_class: Union[Type[Driver], None] = None, log: str = "",
                 log_verbosity: int = 1, title: str = "OAPapers viewer", ):
        """
        Initialization of samples viewer TUI app.

        :param dataset: the dataset for listing that contains all target samples it can also contain source samples
        :param references_dataset: dataset that contains referenced samples, if it is None the targets dataset is used
            instead
        :param items_per_page: maximal number of samples per page
        :param screen: Enable full-screen application mode. Defaults to True.
        :param driver_class: Driver class, or None to use default. Defaults to None.
        :param log: (haven't found doc but probably:) path to log file
        :param log_verbosity: verbosity of logs
        :param title: Title of the application. Defaults to "Textual Application".
        """
        super().__init__(screen, driver_class, log, log_verbosity, title)
        self.dataset = dataset
        self.references_dataset = references_dataset
        if self.references_dataset is None:
            self.references_dataset = self.dataset
        self.items_per_page = items_per_page
        self.body = None
        self.listing_views = ListingView(dataset=self.dataset, items_per_page=self.items_per_page)
        self._action_targets.add("body")    # for calling methods of body object
        self.state = State.LISTING

    async def change_state(self, s: State, **kwargs):
        """
        Performs the change of state. Includes change of views and bindings.

        :param s: the new state
        :param kwargs: additional state dependent arguments
            State.VIEWING:
                document: a document that should be shown
        """

        self.state = s
        self.view.layout.docks = []

        if self.state == State.LISTING:
            self.body = self.listing_views
            self.bindings = ListingView.create_bindings("body.")
            name = "listing"
        elif self.state == State.VIEWING:
            self.body = SampleView(kwargs["document"], self.references_dataset)
            self.bindings = SampleView.create_bindings("body.")
            await self.bind("escape", "go_to_listing", "Back")
            name = f"viewing({kwargs['document'].id})"

        await self.bind("q", "quit", "Quit")

        await self.view.dock(self.body, name=name)
        await self.body.focus()
        self.body.refresh(layout=True)

    async def action_go_to_listing(self):
        await self.change_state(State.LISTING)

    async def on_mount(self, event: events.Mount) -> None:
        await self.change_state(self.state)

    async def show(self, document: Document):
        """
        view sample on given index

        :param document: document that should be shown
        """
        await self.change_state(State.VIEWING, document=document)

    async def on_resize(self, event: events.Resize) -> None:
        await super().on_resize(event)
        await self.body.on_resize(event)




