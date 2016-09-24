# -*- coding: utf-8 -*-

# ---- Imports -----------------------------------------------------------
from traits.api import \
    HasTraits, Str, Button, Instance, List
from traitsui.api import \
    View, UItem, UCustom, HGroup, VGroup, HSplit, VSplit, Tabbed, Include, \
    Menu, MenuBar, Action, ToolBar, ListEditor, spring
from pyface.api import ImageResource

from event_bus import EventBus
# from data_explorer import DataExplorer, model as data_model
# from file_explorer import FileExplorer, model as file_model
from main.console import Console
from main.component import MainUIComponent
from main.event_log import EventLog

from main.console import Console

class DataExplore(MainUIComponent):
    def __init__(self):
        super(DataExplore, self).__init__()
        self.name = u'数据浏览器'

    custom_view = View(
        image=ImageResource('./icons/glyphicons-120-table.png'),
    )


class FileExplore(MainUIComponent):
    def __init__(self):
        super(FileExplore, self).__init__()
        self.name = u'文件浏览器'

    custom_view = View(
        image=ImageResource('./icons/glyphicons-692-tree-structure.png')
    )


class MainUI(HasTraits):
    """ Main window which combines several views
    """

    # navigator tools
    navigators = List(MainUIComponent)

    # tools to operate and view data
    data_area = List(MainUIComponent)

    # auxiliary tools
    auxiliaries = List(MainUIComponent)

    def __init__(self):
        super(MainUI, self).__init__()

        # add file explorer to navigators area
        self.navigators.append(FileExplore())
        # add data explorer to data area
        self.data_area.append(DataExplore())
        # add console and system log to auxiliary tools
        self.auxiliaries.append(Console())
        self.auxiliaries.append(FileExplore())

    # data_explorer = Instance(DataExplorer)
    # file_explorer = Instance(FileExplorer)
    #
    # command_line = Instance(Console)
    # event_log = Instance(EventLog)
    #
    # auxiliary_tools = List(MainUIComponent)
    # def __init__(self, *args, **traits):

    #     super(MainUI, self).__init__(*args, **traits)
    #     self.command_line = Console()
    #     self.event_log = EventLog()
    #     self.auxiliary_tools.append(self.command_line)
    #     self.auxiliary_tools.append(self.event_log)

    # ---- View definition -----------------------------------------------
    # design menu bar
    menu_bar = MenuBar(
        Menu(  # data menu
            Action(
                id='import_data',
                name=u'导入数据...',
                action='import_data'
            ),
            Action(
                id='export_data',
                name=u'导出数据...',
                action='export_data'
            ),
            name=u'数据',
        ),
        Menu(  # view menu
            Action(
                id='hide_file_explorer',
                name=u'隐藏文件浏览器',
                action='_hide_file_explorer'
            ),
            name=u'视图',
        ),
        Menu(  # toolbox menu
            Action(
                id='init_data_generator',
                name=u'数据生成器',
                action='init_data_generator'
            ),
            Action(
                id='init_downloader',
                name=u'数据下载器',
                action='init_downloader'
            ),
            Action(
                id='init_data_reader',
                name=u'数据读取器',
                action='init_data_reader'),
            Action(
                id='init_fitter',
                name=u'拟合器',
                action='init_fitter'
            ),
            Action(
                id='init_filter',
                name=u'滤波器',
                action='init_filter'
            ),
            name=u'工具',
        ),
        Menu(  # help menu
            Action(
                id='show_help_info',
                name=u'帮助信息',
                action='show_help_info'
            ),
            name=u'帮助',
        ),
    )

    # design tool bar
    tool_bar = ToolBar()

    traits_view = View(
        HSplit(
            UCustom(
                'navigators',
                editor=ListEditor(
                    use_notebook=True,
                    show_notebook_menu=True,
                    dock_style='tab',
                    page_name='.name',
                    # deletable=True,
                ),
                width=0.25,
            ),
            VSplit(
                UCustom(
                    'data_area',
                    editor=ListEditor(
                        use_notebook=True,
                        show_notebook_menu=True,
                        dock_style='tab',
                        page_name='.name',
                        # deletable=True,
                    ),
                    height=0.7,
                ),
                UCustom(
                    'auxiliaries',
                    editor=ListEditor(
                        use_notebook=True,
                        show_notebook_menu=True,
                        dock_style='tab',
                        page_name='.name',
                        # deletable=True,
                    ),
                    height=0.3,
                ),
            ),
        ),
        # HSplit(
        #     Tabbed(UCustom(name='file_explorer', width=0.2, label=u'文件浏览器')),
        #
        #     VGroup(
        #
        #         Tabbed(UCustom(name='data_explorer', width=0.8, height=0.7)),
        #         UCustom(
        #             'auxiliary_tools',
        #             editor=ListEditor(
        #                 use_notebook=True,
        #                 show_notebook_menu=True,
        #                 dock_style='tab',
        #                 page_name='.name'
        #             ),
        #             height=0.3,
        #         ),
        #     ),
        # ),
        menubar=menu_bar,
        toolbar=tool_bar,
        width=0.9,
        height=0.9,
        icon=ImageResource('glyphicons-21-home.png', search_path=['../icons']),
        resizable=True,
        title=u'主界面',
    )

    # ------------------------------ #
    #          Menu actions          #
    # ------------------------------ #

    def import_data(self):
        # TODO implement import data menu action
        print 'importing data...'

    def export_data(self):
        # TODO implement export data menu action
        print 'exporting data...'

    def init_data_generator(self):
        # TODO implement init data generator menu action
        print 'initializing data generator...'

    def init_data_reader(self):
        # TODO implement init data reader menu action
        print 'initializing data reader...'

    def init_downloader(self):
        # TODO implement init downloader menu action
        print 'initializing downloader...'
        from toolbox.downloader.downloader_gui import controller
        controller.edit_traits()

    def init_filter(self):
        # TODO implement init filter
        print 'initializing filter...'

    def init_fitter(self):
        # TODO implement init fitter
        print 'initializing fitter...'

    @staticmethod
    def show_help_info():
        from help import help_info
        help_info.edit_traits()


if __name__ == '__main__':
    # from workspace import workspace
    event_bus = EventBus()

    main_ui = MainUI(
        # data_explorer=DataExplorer(
        #     model=data_model(workspace=workspace),
        #     event_bus=event_bus
        # ),
        # file_explorer=FileExplorer(
        #     model=file_model(),
        #     event_bus=event_bus
        # ),
    )

    main_ui.configure_traits()

# EOF
