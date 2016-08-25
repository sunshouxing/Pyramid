# -*- coding: utf-8 -*-

# ---- Imports -----------------------------------------------------------

from traits.api import HasTraits, Instance
from traitsui.api import View, UCustom, Tabbed

from event_bus import EventBus
from data_explorer import DataExplorer, model as data_model
from file_explorer import FileExplorer, model as file_model


class MainWindow(HasTraits):
    """ Main window which combines several views
    """
    data_explorer = Instance(DataExplorer)
    file_explorer = Instance(FileExplorer)

    def __init__(self, *args, **traits):
        super(MainWindow, self).__init__(*args, **traits)

    # ---- View definition -----------------------------------------------
    traits_view = View(
        Tabbed(
            UCustom(name='data_explorer'),
            UCustom(name='file_explorer'),
        ),
        width=600,
        height=700,
        resizable=True,
        title=u'主界面',
    )


if __name__ == '__main__':
    event_bus = EventBus()

    MainWindow(
        data_explorer=DataExplorer(
            model=data_model(
            ),
            event_bus=event_bus
        ),
        file_explorer=FileExplorer(
            model=file_model(
            ),
            event_bus=event_bus
        )
    ).configure_traits()

# EOF
