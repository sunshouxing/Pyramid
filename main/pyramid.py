# -*- coding: utf-8 -*-

# ---- [Imports] ---------------------------------------------------------------
from pyface.api import ImageResource
from traits.api import \
    HasTraits, Instance, List
from traitsui.api import \
    View, UCustom, HSplit, VSplit, Menu, MenuBar, Action, ToolBar, ListEditor

from common import ICONS_PATH
from main.console import Console
from main.data_explorer import DataExplorer, data_model
from main.event_bus import EventBus
from main.file_explorer import FileExplorer, file_model


class MainUI(HasTraits):
    """ Main window which combines several views
    """
    event_bus = Instance(EventBus)

    # navigator tools
    navigators = List(HasTraits)

    # tools to operate and view data
    data_area = List(HasTraits)

    # auxiliary tools
    auxiliaries = List(HasTraits)

    def __init__(self):
        super(MainUI, self).__init__()
        self.event_bus = EventBus()

        # add file explorer to navigators area
        self.navigators.append(FileExplorer(
            model=file_model(), event_bus=self.event_bus
        ))
        # add data explorer to data area
        self.data_area.append(DataExplorer(
            model=data_model(), event_bus=self.event_bus
        ))
        # add console and system log to auxiliary tools
        self.auxiliaries.append(Console())

    # ---- [View definition] ------------------------------------------------
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
                    page_name='.tab_name',
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
                        page_name='.tab_name',
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
        menubar=menu_bar,
        toolbar=tool_bar,
        width=0.9,
        height=0.9,
        icon=ImageResource('glyphicons-21-home.png', search_path=[ICONS_PATH]),
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

    @staticmethod
    def init_downloader():
        from toolbox.downloader.downloader_gui import controller
        controller.edit_traits()

    def init_filter(self):
        # TODO implement init filter
        print 'initializing filter...'

    @staticmethod
    def init_fitter():
        from toolbox.fitter.distribution_fitting_tool import DistributionFittingTool
        DistributionFittingTool().edit_traits()

    @staticmethod
    def show_help_info():
        from help import help_info
        help_info.edit_traits()


if __name__ == '__main__':
    MainUI().configure_traits()

# EOF
