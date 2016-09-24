# -*- coding: utf-8 -*-

from traits.api import HasTraits, Instance, List, Str, Int, Float
from traitsui.api import UItem, UCustom, View, Group, TableEditor, ObjectColumn
from enable.api import ComponentEditor, KeySpec
from chaco.api import ArrayDataSource, LinePlot, Plot, LinearMapper, Legend, PlotAxis
from chaco.tools.api import ZoomTool, PanTool
from chaco.example_support import COLOR_PALETTE
from chaco.scales_tick_generator import ScalesTickGenerator
from chaco.scales.api import CalendarScaleSystem, DefaultScale

from read_history_data import Fields, read_data
from timemodule import DateTime
from legend_highlighter_zoom import LegendHighlighterZoom


class SignalPlot(HasTraits):

    plot = Instance(Plot)

    traits_view = View(
        UItem('plot', editor=ComponentEditor(bgcolor='white')),
        width=800,
        height=400,
        resizable=True)

    def __init__(self, history_data):

        plot = Plot(title=u'Signal Time History')

        i = 0

        for chn in history_data.keys():

            line_plot = LinePlot(
                index=ArrayDataSource(history_data[chn]['time']/1000.0),
                value=ArrayDataSource(history_data[chn]['data']),
                color=COLOR_PALETTE[i],
                index_mapper=LinearMapper(range=plot.index_range),
                value_mapper=LinearMapper(range=plot.value_range)
            )

            plot.add(line_plot)
            plot.plots[chn] = [line_plot]

            plot.index_range.sources.append(line_plot.index)
            plot.value_range.sources.append(line_plot.value)

            i += 1

        plot.value_range.low_setting = 'auto'
        plot.value_range.high_setting = 'auto'
        plot.value_range.tight_bounds = False
        plot.value_range.margin = 0.05
        plot.value_range.refresh()

        plot.index_axis = PlotAxis(
            title=u'Time',
            title_spacing=30,
            orientation='bottom',
            mapper=plot.index_mapper,
            tick_in=0,
            tick_generator=ScalesTickGenerator(scale=CalendarScaleSystem())
        )
        plot.value_axis = PlotAxis(
            title=u'Amplitude',
            title_spacing=30,
            orientation='left',
            mapper=plot.value_mapper,
            tick_in=0,
            tick_generator=ScalesTickGenerator(scale=DefaultScale())
        )

        legend = Legend(
            component=plot,
            align='ur',
            padding=5,
            line_spacing=10)
        legend.plots = plot.plots
        legend.tools.append(LegendHighlighterZoom(
            component=legend,
            drag_botton='right',
            dim_factor=10,
            line_scale=1.0))
        plot.overlays.append(legend)

        plot.tools.append(PanTool(plot))
        plot.overlays.append(ZoomTool(
            component=plot,
            always_on_modifier='control',
            prev_state_key=KeySpec('Left', 'control'),
            next_state_key=KeySpec('Right', 'control')))

        self.plot = plot


class SignalInfo(HasTraits):
    channel = Str
    start_time = Str
    end_time = Str
    sample_count = Int
    maximum = Float
    minimum = Float


class SignalInfoTable(HasTraits):

    signal_info_list = List(SignalInfo)

    table_editor = TableEditor(
        columns=[
            ObjectColumn(
                name='channel',
                label=u'通道名称',
                horizontal_alignment='center',
                style='custom',
                width=0.2),
            ObjectColumn(
                name='start_time',
                label=u'起始时间',
                horizontal_alignment='center',
                style='custom',
                width=0.3),
            ObjectColumn(
                name='end_time',
                label=u'结束时间',
                horizontal_alignment='center',
                style='custom',
                width=0.3),
            ObjectColumn(
                name='sample_count',
                label=u'采样点数',
                horizontal_alignment='center',
                style='custom',
                width=0.2)],
        editable=False, sortable=True, row_factory=SignalInfo)

    traits_view = View(
        Group(UItem('signal_info_list', editor=table_editor)),
        width=800, height=150, resizable=True)

    def __init__(self, history_data):

        self.signal_info_list = []
        for channel in history_data.keys():
            signal_info = SignalInfo()
            signal_info.channel = channel
            signal_info.sample_count = history_data[channel]['time'].__len__()
            signal_info.start_time = DateTime.fromtimestamp(history_data[channel]['time'][0]/1000) \
                .strftime('%Y-%m-%d %H:%M:%S')
            signal_info.end_time = DateTime.fromtimestamp(history_data[channel]['time'][-1]/1000) \
                .strftime('%Y-%m-%d %H:%M:%S')
            signal_info.maximum = history_data[channel]['data'].max()
            signal_info.minimum = history_data[channel]['data'].min()

            self.signal_info_list.append(signal_info)


class DataFigure(HasTraits):

    signal_plot = Instance(SignalPlot)
    signal_info_table = Instance(SignalInfoTable)

    traits_view = View(
        UCustom('signal_plot'), UCustom('signal_info_table')
    )

    def __init__(self, data):
        self.signal_plot = SignalPlot(data)
        self.signal_info_table = SignalInfoTable(data)


if __name__ == '__main__':

    input_dict = {
        'root': '/home/arthur/Downloads/data/',  # root和“文件根目录”相对应
        'sensor_channel': ('SEW1111-DX', 'SEW1112-DX', 'SEW1113-DX'),  # sensor_channel和“传感器通道”相对应
        'start_time': '2015-09-01 00:00:00',  # start_time和“开始日期”相对应
        'end_time': '2015-09-01 23:00:00',  # end_time和“结束日期”相对应
    }

    fields = Fields(**input_dict)
    history_data = read_data(fields)

    main_form = DataFigure(history_data)
    main_form.configure_traits()

# EOF
