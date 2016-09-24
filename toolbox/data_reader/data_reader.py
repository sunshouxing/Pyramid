# -*- coding: utf-8 -*-

# ---- Imports -----------------------------------------------------------
from traits.api import *
from traitsui.api import *
from pyface.api import ImageResource

from date_time_trait import DateTime
from plot_history_data import DataFigure
from read_history_data import Fields, read_data


class DataSpec(HasTraits):
    # the root directory contains downloaded data
    root = Directory

    # description of the root directory's structure to
    # help the data reader to find the data files
    root_structure = Unicode

    # the time data start from
    start_time = Instance(DateTime, ())

    # the time data end to
    end_time = Instance(DateTime, ())

    # the bridge's name
    bridge = Unicode

    # channels list to read data from
    channels = List(Unicode)

    # whether ready to read data
    ready_to_read = Property(Bool)

    @property_depends_on('root,channels,start_time,end_time')
    def _get_ready_to_read(self):
        return (self.root is not None) and \
               (len(self.channels) > 0) and \
               (self.start_time is not None and self.end_time is not None)


class _RootStructureHandler(Handler):
    model = Instance(HasTraits)

    def init(self, info):
        self.model = info.object

    def object_data_path_changed(self, info):
        sub_dirs = [sub_dir for sub_dir in self.model.data_path.split('/') if sub_dir.strip()]
        self.model.path_tree = \
            u'\n'.join([u'{}|_ {}'.format(' ' * 4 * index, directory)
                        for index, directory in enumerate(sub_dirs)])
        info.ui.get_editors('path_tree')[0].update_editor()


class _RootStructure(HasTraits):
    statement = u'''
    说明：
        请参照示例中数据信息和描述格式, 并按实际情况描述数据文件在根目录中的路径, 以让数据读取器快速准确地定位数据文件.

    示例：
        数据信息
            □ 根目录：D:/data/
            □ 桥梁：闵浦二桥
            □ 日期：2016.09.03
            □ 传感器：SAD0101
            □ 通道：SAD0101-DX
        描述示例：
            1. D:/data/监测数据/闵浦二桥/2016/0903/SAD0101/
            2. D:/data/闵浦二桥/数据/20160903/SAD0101-DX/
    '''
    # the user input data path
    data_path = File

    # a variant of data_path to demonstrate root structure
    path_tree = Unicode

    # an abstract description of data_path, used to format
    # data's real path with parameters, e.g. bridge, date, time, sensors
    data_spec = Instance(DataSpec)
    path_desc = DelegatesTo('data_spec', prefix='root_structure')

    traits_view = View(
        Group(
            UCustom('statement', editor=HTMLEditor(format_text=True)),
            '_'
        ),
        Item('data_path', style='text', label=u'路径描述'),
        UReadonly('path_tree', height=250),
        handler=_RootStructureHandler,
        buttons=['OK'],
        height=620,
    )

    def _data_path_changed(self):
        mapping = {
            u'D:/data': u'{root}',
            u'闵浦二桥': u'{bridge}',
            u'2016': u'{datetime:%Y}',
            u'09': u'{datetime:%m}',
            u'03': u'{datetime:%d}',
            u'SAD0101-DX': u'{channel}',
            u'SAD0101': u'{sensor}',
        }

        self.path_desc = unicode(self.data_path)
        for original, field in mapping.items():
            self.path_desc = self.path_desc.replace(original, field)


class DataReader(Controller):
    # button to config root structure
    button_for_root_structure = Button(
        style='toolbar',
        image=ImageResource('../../icons/glyphicons-692-tree-structure.png'),
    )

    # button to start to read data
    button_for_read = Button(u'读取数据')

    # path example to show root directory structure
    path_example = Str

    # candidate bridges to select from
    all_bridges = List(Str)

    # candidate channels to select from
    all_channels = List(Str)

    # figure and generic info of data have been read
    data_figure = Instance(DataFigure)

    # main traits view to config data reader parameters
    traits_view = View(
        HGroup(
            '10',
            VGroup(
                '10',
                HGroup(  # for root directory
                    VGroup(
                        HGroup(
                            UItem(
                                'root',
                                has_focus=True,
                                tooltip=u'根目录选择',
                            ),
                            '_',
                            UCustom(
                                'handler.button_for_root_structure',
                                tooltip=u'根目录结构设置...',
                            ),
                        ),
                    ),
                    label=u'目录设置',
                    show_border=True,
                ),
                '10',
                HGroup(  # for start and end time
                    spring,
                    VGroup(
                        Label(u'开始'),
                        UCustom('object.start_time'),
                    ),
                    spring,
                    VGroup(
                        Label(u'结束'),
                        UCustom('object.start_time'),
                    ),
                    spring,
                    label=u'起止时间',
                    show_border=True,
                ),
                '10',
                VGroup(  # for bridge and channels selection
                    # bridge selection
                    HGroup(
                        Label(u'桥梁选择'),
                        UItem(
                            'bridge',
                            editor=EnumEditor(name='handler.all_bridges'),
                        ),
                    ),
                    ' ', '_', ' ',
                    # channels selection
                    UItem(
                        'channels',
                        editor=SetEditor(
                            name='handler.all_channels',
                            left_column_title=u'传感器列表',
                            right_column_title=u'已选传感器',
                        )
                    ),
                    label=u'桥梁及通道选择',
                    show_border=True,
                ),
                HGroup(  # for button for reading data
                    spring, UItem('handler.button_for_read', enabled_when='ready_to_read')
                ),
                # UCustom('handler.data_figure'),
                '10',
            ),
            '10',
        ),
        resizable=True,
        title=u'数据读取器',
    )

    @on_trait_change('button_for_root_structure')
    def config_root_structure(self):
        _RootStructure(data_spec=self.model).edit_traits()

    @on_trait_change('button_for_read')
    def read_data(self):
        data = read_data(Fields(**{
            'root': self.model.root,
            'path': self.model.root_structure,
            'sensor_channel': self.model.channels,
            'start_time': self.model.start_time,
            'end_time': self.model.end_time,
        }))
        DataFigure(data).edit_traits()

    def _root_structure_set_changed(self):
        print self.root_structure_set

    def _all_bridges_default(self):
        # TODO how to acquire bridges to read data from
        return ['SEW1111-DX', 'SEW1112-DX', 'SEW1113-DX', 'SEW1114-DX', 'SEW1115-DX']

    def _all_channels_default(self):
        # TODO how to acquire channels to read data from
        return ['SEW1111-DX', 'SEW1112-DX', 'SEW1113-DX', 'SEW1114-DX', 'SEW1115-DX']


if __name__ == '__main__':
    data_spec = DataSpec()
    DataReader(data_spec).configure_traits()

    # _RootStructure().configure_traits()

# EOF
