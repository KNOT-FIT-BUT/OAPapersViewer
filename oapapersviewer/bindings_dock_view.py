# -*- coding: UTF-8 -*-
""""
Created on 01.08.22

This module contains ABC DockView class that also provides key bindings.

:author:     Martin Dočekal
"""
from abc import ABC, abstractmethod

from textual.binding import Bindings
from textual.views import DockView


class BindingsDockView(DockView, ABC):
    """
    Doc view with bindings.
    """

    @staticmethod
    @abstractmethod
    def create_bindings(action_prefix: str = "") -> Bindings:
        """
        Creates new bindings object that contains necessary bindings to use this view.

        :param action_prefix: prefix for action naming
        """
        pass