# -*- coding: utf-8 -*-

# ---- Imports -----------------------------------------------------------
from traits.api import HasTraits, Instance
from traitsui.api import Item, View, UCustom, Tabbed, HGroup, VGroup, HSplit, VSplit, \
    Menu, MenuBar, Action, ActionGroup, ToolBar

from pyface.image_resource import ImageResource

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
    # design menu bar
    menu_bar = MenuBar(
        Menu(
            Action(id='import_data', name=u'导入数据...', action="import_data"),
            Action(id='export_data', name=u'导出数据...', action="export_data"),
            name=u'数据',
        ),
        Menu(
          name=u'工具箱',
        ),
        Menu(
            Action(id='hide_file_explorer', name=u'隐藏文件浏览器', action='_hide_file_explorer'),
            name=u'视图',
        ),
        Menu(
            name=u'帮助',
        ),
    )

    # design tool bar
    tool_bar = ToolBar(
        Action(
            image=ImageResource("folder_page.png", search_path=["img"]),
            tooltip="Print Figure",
            action="print_figure"
        ),
        Action(
            image=ImageResource("disk.png", search_path=["img"]),
            tooltip="Zoom In",
            action="zoom_in"
        ),
        Action(
            image=ImageResource("disk.png", search_path=["img"]),
            tooltip="Zoom Out",
            action="zoom_out"
        ),
        Action(
            image=ImageResource("disk.png", search_path=["img"]),
            tooltip="Pan",
            action="pan"
        ),
        Action(
            image=ImageResource("disk.png", search_path=["img"]),
            tooltip="Legend On/Off",
            action="zoom_out"
        ),
        Action(
            image=ImageResource("disk.png", search_path=["img"]),
            tooltip="Grid On/Off",
            action="zoom_out"
        ),
        Action(
            image=ImageResource("disk.png", search_path=["img"]),
            tooltip="Restore Default Axes Limits",
            action="zoom_out"
        ),
    )

    traits_view = View(
        '10',
        HSplit(
            UCustom(name='file_explorer', width=0.2),
            VGroup(
                UCustom(name='data_explorer', width=0.7, height=50),
                VSplit(
                    UCustom(name='data_explorer', height=0.5),
                    Tabbed(
                        UCustom(name='data_explorer'),
                        UCustom(name='data_explorer'),
                    )
                )
            ),
            # UCustom(name='data_explorer', width=0.7),
        ),
        menubar=menu_bar,
        toolbar=tool_bar,
        width=1.0,
        height=1.0,
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
        ),

    ).configure_traits()

# EOF
