# -*- coding: utf-8 -*-

# ---- [Imports] ---------------------------------------------------------------

from pyface.api import ImageResource
from traits.api import \
    HasTraits, SingletonHasTraits, HTML, Enum, Instance, List
from traitsui.api import \
    View, Controller, UItem, UCustom, HSplit, VSplit, \
    Menu, MenuBar, Action, ToolBar, ListEditor, HTMLEditor

from common import ICONS_PATH
from main.console import Console
from main.data_explorer import DataExplorer, data_model
from main.event_bus import EventBus
from main.event_log import event_log
from main.file_explorer import FileExplorer, file_model

_notice_text = u'''
系统退出后，尚未保存的数据将丢失无法恢复！

单击【返回】按钮，返回系统保存数据；单击【退出】按钮，直接退出。
'''


class _ConfirmInfo(SingletonHasTraits):
    # confirm info of retreating to save data or existing directly
    state = Enum('RETREAT', 'EXIST')


class _ConfirmInfoController(Controller):

    notice = HTML(_notice_text)

    retreat_action = Action(
        id='retreat_action_id',
        name=u'返回',
        action='retreat',
    )

    exist_action = Action(
        id='exist_action_id',
        name=u'退出',
        action='exist',
    )

    traits_view = View(
        UItem('handler.notice', editor=HTMLEditor(format_text=True)),
        buttons=[retreat_action, exist_action],
        width=550,
        height=150,
        title=u'提示信息',
        kind='modal',
    )

    def retreat(self, info):
        self.model.state = 'RETREAT'
        info.ui.control.close()

    def exist(self, info):
        self.model.state = 'EXIST'
        info.ui.control.close()


class MainUIController(Controller):
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
    tool_bar = ToolBar(
        Action(
            image=ImageResource('glyphicons-73-bookmark.png', search_path=[ICONS_PATH]),
            tooltip=u'收藏夹',
            action='manage_bookmarks'
        ),
        Action(
            image=ImageResource('glyphicons-359-file-import.png', search_path=[ICONS_PATH]),
            tooltip=u'导入数据',
            action='import_data'
        ),
        Action(
            image=ImageResource('glyphicons-360-file-export.png', search_path=[ICONS_PATH]),
            tooltip=u'导出数据',
            action='export_data'
        ),
        Action(
            image=ImageResource('glyphicons-365-cloud-download.png', search_path=[ICONS_PATH]),
            tooltip=u'数据下载器',
            action='init_downloader'
        ),
        Action(
            image=ImageResource('glyphicons-416-disk-open.png', search_path=[ICONS_PATH]),
            tooltip=u'数据读取器',
            action='init_data_reader'
        ),
        Action(
            image=ImageResource('glyphicons-42-charts.png', search_path=[ICONS_PATH]),
            tooltip=u'数据生成器',
            action='init_data_generator'
        ),
        Action(
            image=ImageResource('glyphicons-790-filter-applied.png', search_path=[ICONS_PATH]),
            tooltip=u'滤波器',
            action='init_filter'
        ),
        Action(
            image=ImageResource('glyphicons-41-stats.png', search_path=[ICONS_PATH]),
            tooltip=u'拟合器',
            action='init_fitter'
        ),
        Action(
            image=ImageResource('glyphicons-488-fit-image-to-frame.png', search_path=[ICONS_PATH]),
            tooltip=u'全屏',
            action='zoom_out'
        ),
        Action(
            image=ImageResource('glyphicons-487-fit-frame-to-image.png', search_path=[ICONS_PATH]),
            tooltip=u'退出全屏',
            action='zoom_out'
        ),
        Action(
            image=ImageResource('glyphicons-281-settings.png', search_path=[ICONS_PATH]),
            tooltip=u'设置',
            action='zoom_out'
        ),
        Action(
            image=ImageResource('glyphicons-122-message-empty.png', search_path=[ICONS_PATH]),
            tooltip=u'联系我们',
            action='zoom_out'
        ),
    )

    traits_view = View(
        HSplit(
            UCustom(
                'navigators',
                editor=ListEditor(
                    use_notebook=True,
                    show_notebook_menu=True,
                    dock_style='tab',
                    page_name='.tab_name',
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
                    ),
                    height=0.7,
                ),
                UCustom(
                    'auxiliaries',
                    editor=ListEditor(
                        use_notebook=True,
                        show_notebook_menu=True,
                        dock_style='tab',
                        page_name='.tab_name',
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
    #    Menu & Toolbar actions      #
    # ------------------------------ #

    def import_data(self):
        # TODO implement import data menu action
        print 'importing data...'

    def export_data(self):
        # TODO implement export data menu action
        print 'exporting data...'

    @staticmethod
    def init_data_reader(info):
        from toolbox.data_reader.data_reader import data_reader
        data_reader.edit_traits()

    @staticmethod
    def init_filter(info):
        from toolbox.filter.filter_view_multi import signal_filter
        signal_filter.edit_traits()

    @staticmethod
    def init_downloader(info):
        from toolbox.downloader.downloader_gui import downloader
        downloader.edit_traits()

    @staticmethod
    def init_fitter(info):
        from toolbox.fitter.distribution_fitting_tool import fitter
        fitter.edit_traits()

    @staticmethod
    def init_data_generator(info):
        from toolbox.generator.random_data_generator import data_generator
        data_generator.edit_traits()

    @staticmethod
    def show_help_info(info):
        from main.help import help_info
        help_info.edit_traits()

    @staticmethod
    def manage_bookmarks(info):
        from main.book_marks import bookmark_manager
        bookmark_manager.edit_traits()

    def close(self, info, is_ok):
        confirm_info = _ConfirmInfo()
        _ConfirmInfoController(model=confirm_info).edit_traits()

        if confirm_info.state == 'EXIST':
            return super(MainUIController, self).close(info, True)


class MainUI(HasTraits):
    """ Main window which combines several views
    """
    # the event bus between file system and data space
    event_bus = Instance(EventBus)

    # navigator tools (including file explorer now)
    navigators = List(HasTraits)

    # tools to operate and view data (including data list and data inspector)
    data_area = List(HasTraits)

    # auxiliary tools (include console and event log)
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
        self.auxiliaries.append(event_log)


if __name__ == '__main__':
    MainUIController(model=MainUI()).configure_traits()

# EOF
