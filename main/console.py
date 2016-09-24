# -*- coding: utf-8 -*-

# ---- [Imports] ---------------------------------------------------------------
from traits.api import Str, List, Dict, Event, Bool
from traitsui.api import HGroup, UItem, ShellEditor

import workspace
from main.component import MainUIComponent


class Console(MainUIComponent):
    environment = Dict

    # record history commands for future review
    command_to_execute = Event
    command_executed = Event(Bool)
    history_commands = List(Str)

    custom_view = HGroup(
        UItem(
            'environment',
            editor=ShellEditor(
                share=True,
                command_executed='command_executed',
                command_to_execute='object.command_to_execute'
            ),
            has_focus=True,
            tooltip=u'请输入数据操作语句并按回车结束',
        ),
    )

    def __init__(self, *args, **traits):
        super(Console, self).__init__(*args, **traits)
        self.name = u'控制台'
        self.environment = workspace.get_data()


if __name__ == '__main__':
    console = Console()
    console.configure_traits()

# EOF
