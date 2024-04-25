# -*- coding: UTF-8 -*-
""""
Created on 29.07.22

:author:     Martin Dočekal
"""
import enum
from typing import Optional

from textual.views import DockView
from textual.widgets import Footer
from .inputs import TextInput, IntegerInput


class PromptFormat(enum.Enum):
    """
    all prompt input formats
    """
    TEXT = enum.auto()
    INTEGER = enum.auto()


class FooterView(DockView):
    """
    Footer layout.
    """
    def __init__(self, name: Optional[str] = None) -> None:
        """
        initialization of prompt footer

        :param name: name of view
        """
        super().__init__(name=name)
        self.prompt = None
        self.layout_size = 1

    async def prompting(self, prompt_text: str, p_format: PromptFormat = PromptFormat.TEXT):
        """
        activates prompting state

        :param prompt_text: the text that explains your prompt
        :param p_format: format of input
        """
        if p_format == PromptFormat.TEXT:
            self.prompt = TextInput(prompt=prompt_text, style="white")
        elif p_format == PromptFormat.INTEGER:
            self.prompt = IntegerInput(prompt=prompt_text, style="white")
        else:
            raise NotImplementedError("Something is rotten in the state of this program.")
        self.layout.docks = []
        await self.dock(self.prompt)
        await self.prompt.focus()

    async def hints(self):
        """
        activates hints showing footer
        """
        self.layout.docks = []
        if self.app.focused == self.prompt:
            await self.app.set_focus(None)
        self.prompt = None
        await self.dock(Footer())


