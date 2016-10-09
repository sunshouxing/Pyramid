# -*- coding: utf-8 -*-

# ---- Imports -----------------------------------------------------------
from traits.api import HasTraits, Enum, Any


class EventBus(HasTraits):
    command = Enum('NONE', 'IMPORT_DATA', 'EXPORT_DATA', 'EXPORT_SELECTED_DATA')
    args = Any()

    def fire_event(self, command, args=None):
        # set args value first to avoid invoke event handler with None args
        self.args = args
        self.command = command

# EOF
