# -*- coding: utf-8 -*-

# ---- Imports -----------------------------------------------------------
from traits.api import Str, List, Dict, Event, Bool
from traitsui.api import HGroup, VGroup, UItem, ShellEditor

from main.component import MainUIComponent
import workspace


class Console(MainUIComponent):
    environment = Dict

    # record history commands for future review
    command_to_execute = Event
    command_executed = Event(Bool)
    history_commands = List(Str)

    custom_view = HGroup(
        VGroup(UItem('history_commands')),
        '_',
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
        self.name = u'命令行'
        self.environment = workspace.get_data()

    def _command_executed_fired(self, command):
        # FIXME delete debug info
        print 'command executed changed: ', command
        # self.history_commands.append(self.command_executed)

    def _command_to_execute_fired(self, command):
        # FIXME delete debug info
        print 'command to execute changed: ', command


if __name__ == '__main__':
    console = Console()
    console.configure_traits()

# EOF
