# -*- coding: UTF-8 -*-
""""
Created on 29.07.22
Module containing inputs.

:author:     Martin Dočekal
"""
from typing import Optional, Any, Union

import textual_inputs
from rich.console import RenderableType
from rich.panel import Panel
from rich.style import Style
from rich.text import Text


class TextInput(textual_inputs.TextInput):
    """
    A simple text input widget.

    Just overrides rending that is used in its parent.
    """

    def __init__(self, style: Union[str, Style] = "", prompt: str = "", name: Optional[str] = None, value: str = "",
                 password: bool = False, syntax: Optional[str] = None, **kwargs: Any) -> None:
        """
        initialization of input

        :param style: text style
        :param prompt: The prompt for user that will be written before cursor
        :param name: The unique name of the widget. If None, the widget will be automatically named.
        :param value: Defaults to "". The starting text value.
        :param password: Defaults to False. Hides the text input, replacing it with bullets.
        :param syntax: The name of the language for syntax highlighting.
        :param kwargs: additional ones
        """
        super().__init__(name=name, value=value, title=prompt, password=password, syntax=syntax,  **kwargs)

        self.text_style = style

    def render(self) -> RenderableType:
        panel: Panel = super().render()

        return Text.assemble(self.title+": ", panel.renderable, style=self.text_style)


class IntegerInput(textual_inputs.IntegerInput):
    """
    A simple integer input widget.

    Just overrides rending that is used in its parent.
    """

    def __init__(self, style: Union[str, Style] = "", prompt: str = "", name: Optional[str] = None,
                 value: Optional[int] = None, step: int = 1,) -> None:
        """
        initialization of input

        :param style: text style
        :param prompt: The prompt for user that will be written before cursor
        :param name: The unique name of the widget. If None, the widget will be automatically named.
        :param value: Defaults to "". The starting text value.
        :param step: step that is used when incrementing using key arrows
        """
        super().__init__(name=name, value=value, title=prompt, step=step)

        self.text_style = style

    def render(self) -> RenderableType:
        panel: Panel = super().render()

        return Text.assemble(self.title + ": ", panel.renderable, style=self.text_style)
