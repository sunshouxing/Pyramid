# -*- coding: utf-8 -*-

# ---- [Imports] ---------------------------------------------------------------
from traits.api import \
    HasTraits, Bool, Str, Instance, List, Event, DelegatesTo
from traitsui.api import \
    View, UItem, HGroup, ShellEditor

from main.workspace import Workspace, workspace


class Console(HasTraits):
    workspace = Instance(Workspace)
    environment = DelegatesTo('workspace', prefix='data_space')

    # record history commands for future review
    command_to_execute = Event
    command_executed = Event(Bool)
    history_commands = List(Str)

    traits_view = View(
        HGroup(
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
        ),
    )

    def __init__(self, *args, **traits):
        super(Console, self).__init__(*args, **traits)
        self.tab_name = u'控制台'
        self.workspace = workspace


if __name__ == '__main__':
    console = Console()
    console.configure_traits()

# EOF
