# -*- coding: utf-8 -*-

# ---- Imports -----------------------------------------------------------

from traits.api import HasTraits, Instance
from traitsui.api import View, Item, HGroup

from event_bus import EventBus
import var_explorer_se as _vexp
import file_explorer as _fexp


view = View(
    HGroup(
        Item(
            name='var_explorer_tab',
            style='custom',
            show_label=False,
        ),
        Item(
            name='file_explorer_tab',
            style='custom',
            show_label=False,
        ),
        orientation='horizontal',
        layout='tabbed',
        springy=True
    ),  # Tabbed(  # Item(  # 	name='var_explorer_tab',  # ),  # Item(  # 	name='file_explorer_tab',  # ),  #),
    width=600,
    height=700,
    resizable=False,
    title=u'Main',
)


class MainWindow(HasTraits):
    """ Main window which combines several views """
    var_explorer_tab = Instance(_vexp.VariableExplorer)
    file_explorer_tab = Instance(_fexp.FileExplorer)
    view = view


if __name__ == '__main__':
    event_bus = EventBus()

    MainWindow(
        var_explorer_tab=_vexp.VariableExplorer(
            model=_vexp.model(
            ),
            event_bus=event_bus
        ),
        file_explorer_tab=_fexp.FileExplorer(
            model=_fexp.model(
            ),
            event_bus=event_bus
        )
    ).configure_traits()

# EOF
