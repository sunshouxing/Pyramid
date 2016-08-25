# -*- coding: utf-8 -*-

# ---- Imports -----------------------------------------------------------
from traits.api import HasTraits, Any, Str


class EventBus(HasTraits):
    command = Str('')
    args = Any()

    def fire_event(self, command, args=None):
        self.command = command
        self.args = args

# EOF
