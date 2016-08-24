# -*- coding: utf-8 -*-

# from traits.etsconfig.api import ETSConfig
# ETSConfig.toolkit = 'qt4'

from traits.api \
    import HasTraits, Bool, Float, List, Instance, Button, on_trait_change
from traitsui.api \
    import View, Item, HGroup, VGroup, TableEditor, ObjectColumn
from chaco.api \
    import VPlotContainer
from chaco.tools.api \
    import RangeSelection, RangeSelectionOverlay, LegendHighlighter
from enable.api \
    import LineStyle, ColorTrait, ComponentEditor
from numpy import array

from comm import *
import fft_filter as fil


# ############################################
# Custom data models, components, controllers
# ############################################
class RangeModel(HasTraits):
    """
    Data model - the frequency range 
    (physical units, not screen coordinates)
    """

    active = Bool(True)
    focused = Bool(True)  # Flag that indicates the mouse input
    lower = Float(0)
    upper = Float(0)

    _last_counter = 1

    def __init__(self, lower=None, upper=None, *args, **kwargs):
        super(RangeModel, self).__init__(*args, **kwargs)

        self.lower = lower or 0
        self.upper = upper or 0

        self._counter = self.__class__._last_counter
        self.__class__._last_counter += 1

    def __str__(self):
        return '{}{}:({}, {})'.format(
            self.__class__.__name__,
            self._counter,
            self.lower,
            self.upper)


class RangeOverlay(RangeSelectionOverlay):
    """
    Visible screen region which allows to
    switch back into selected state after selection is complete
    """

    lower = Float(0)
    upper = Float(0)
    focused = Bool(True)
    focused_border_style = LineStyle('solid')
    focused_fill_color = ColorTrait('dodgerblue')
    range_data = Instance(RangeModel)

    _last_counter = 1

    def __init__(self, component=None, upper=None, lower=None, *args, **kwargs):
        super(RangeOverlay, self).__init__(component, *args, **kwargs)

        self.lower = lower or 0
        self.upper = upper or 0
        self.range_data = kwargs['rangedata']
        self.name = '{}{}'.format(self.__class__.__name__, self.__class__._last_counter)
        self.__class__._last_counter += 1

    def request_redraw(self):
        # ask redraw:
        self.plot.request_redraw()

    @on_trait_change('range_data.active, range_data.lower, range_data.upper')
    def _handle_range_changes(self):
        self.request_redraw()

    @on_trait_change('focused')
    def _handle_focused(self):
        # ask redraw:
        print '@on_trait_change: {}.focused={}'.format(self.name, self.focused)
        self.rangedata.focused = self.focused
        # self.request_redraw()

    @on_trait_change('lower')
    def _handle_lower(self):
        # ask redraw:
        print "@on_trait_change: LOWER: ", self.name, " coords:", self.lower
        self.rangedata.lower = self.lower
        # self.request_redraw()

    @on_trait_change('upper')
    def _handle_upper(self):
        # ask redraw:
        print "@on_trait_change: UPPER: ", self.name, " coords:", self.upper
        self.rangedata.upper = self.upper
        # self.request_redraw()

    def contains_point(self, point):
        coords = self._get_selection_screencoords()
        x1, x2 = coords[0]
        axis_ndx = self.axis_index
        value = point[axis_ndx]
        print(self.lower, '<=', value, '<=', self.upper)
        print(x1, '<=', value, '<=', x2)
        return (x1 <= value <= x2)

    def _get_selection_screencoords(self):
        # print ('coords:')

        return [self.mapper.map_screen(array([self.lower, self.upper]))]

    def overlay(self, component, gc, view_bounds=None, mode='normal'):
        """ Draws this component overlaid on another component. Overrides AbstractOverlay. """
        axis_ndx = self.axis_index
        lower_left = [0, 0]
        upper_right = [0, 0]

        if not self.rangedata.active:
            return
        # print
        # print(repr(gc), dir(gc))
        # print(help(gc.set_fill_color))
        # print

        # for coord in self.coordinate:
        # Draw the selection
        coords = self._get_selection_screencoords()
        for coord in coords:
            (start, end,) = coord
            lower_left[axis_ndx] = start
            lower_left[1 - axis_ndx] = component.position[(1 - axis_ndx)]
            upper_right[axis_ndx] = end - start
            upper_right[1 - axis_ndx] = component.bounds[(1 - axis_ndx)]
            with gc:
                # print self.focused_fill_color, self.fill_color_, self.focused_fill_color_
                # print self.focused_border_style, self.border_style_, self.focused_border_style_

                gc.clip_to_rect(component.x, component.y, component.width, component.height)
                gc.set_alpha(self.alpha)
                gc.set_fill_color(self.focused_fill_color_ if self.focused else self.fill_color_)
                gc.set_stroke_color(self.border_color_)
                gc.set_line_width(self.border_width)
                gc.set_line_dash(self.border_style_)
                # gc.set_line_dash(self.focused_border_style_ if self.focused else self.border_style_)
                gc.draw_rect((lower_left[0],
                              lower_left[1],
                              upper_right[0],
                              upper_right[1]))


class RangeController(RangeSelection):
    """
    RangeSelection which allows to edit multiple data ranges
    """

    # Instance count
    _last_counter = 0

    focused = Bool(True)

    # children overlay - visible region on the plot

    focused_overlay = Instance(RangeOverlay)

    def __init__(self, *args, **kwargs):
        super(RangeController, self).__init__(*args, **kwargs)

        self._counter = self.__class__._last_counter
        self.__class__._last_counter += 1

        self.name = '{} {}'.format(self.__class__.__name__, self._counter)

        # refernce to main storage for dataranges:    
        self._ranges = kwargs['rangeslist']
        self._overlays = kwargs['overlayslist']

        print('component', self.component)
        print('self._overlays', repr(self._overlays))

        # self.auto_handle_events = False

        # self.add_range_objects()

    @property
    def overlays(self):
        """ Reference to list of overlays (usually curve.overlays)"""
        return self._overlays

    @property
    def ranges(self):
        """Reference to external list of ranges"""
        return self._ranges

    @on_trait_change('event_state')
    def _handle_event_state(self):
        print "STATE", self.event_state

    def add_range_objects(self, lower=None, upper=None):
        """
        Starts new range, adds both the physical data range 
        and the visible screen overlay.
        """
        print "adding objects, ", lower, upper

        rangemodel = RangeModel(
            lower=lower,
            upper=upper
        )
        overlay = RangeOverlay(
            component=self.component,
            lower=lower,
            upper=upper,
            rangedata=rangemodel
        )
        # Append range and overlay to their collections:
        self.overlays.append(overlay)
        self.ranges.append(rangemodel)
        # Make new overlay focused:
        self.focused_overlay = overlay

    def focus_overlay_by_point(self, point):
        """
        Focus "topmost" overlay which contains this screen point
        """
        self.focused_overlay = None
        z_order = self.overlays[:]
        z_order.reverse()
        for overlay in z_order:
            if overlay.contains_point(point):
                overlay.focused = True
                self.focused_overlay = overlay
                print "found!"
            else:
                overlay.focused = False
        return self.focused_overlay is not None

    def _get_selection_screencoords(self):
        """ Returns a tuple of (x1, x2) screen space coordinates of the start
        and end selection points.

        If there is no current selection, then it returns None.
        """
        selection = self.selection
        if selection is not None and len(selection) == 2:
            return self.mapper.map_screen(array(selection))
        else:
            return None

    @on_trait_change('focused')
    def _handle_focused(self):
        """
        Sync model state (is focused)
        """
        # print "@on_trait_change: RangeSelection: ", self.name," focused", self.focused
        # update state or connected overlay
        if self.overlay:
            self.overlay.focused = self.focused

    @on_trait_change('selection')
    def _handle_selection_changes(self):
        """
        Sync model values
        """
        selection = self.selection
        print "@on_trait_change: SELECTION_XY: ", self.name, " selection", selection
        if selection is not None and len(selection) == 2:
            if self.focused_overlay:
                self.focused_overlay.lower = min(*selection)
                self.focused_overlay.upper = max(*selection)

    def deselect(self, event=None):
        """ Deselects the highlighted region."""
        if self.focused_overlay:
            self.focused_overlay.focused = False
        self.focused_overlay = None
        super(RangeController, self).deselect(event)

    def normal_left_down(self, event):
        """
        Try to find the containing overlay
        """
        print "normal_left_down"
        # Try to find overlay which under the mouse cursor:
        if self.focus_overlay_by_point((event.x, event.y)):
            # Update selection to the actual range of data/overlay:
            self.selection = (self.focused_overlay.lower, self.focused_overlay.upper)
            # Allow to move range as a whole or to change its bounds:
            self.event_state = 'selecting'
            return
        # Nothing found, so create a new range here
        self.add_range_objects()
        # Call inherited method:
        super(RangeController, self).normal_left_down(event)


table_editor = TableEditor(
    columns=[
        ObjectColumn(
            name="active",
            label=u"是否使用",
            horizontal_alignment="center",
            style="custom",
            format_func=lambda b: b and u"√" or u" ",
            width=0.06
        ),
        ObjectColumn(
            name="lower",
            label=u"区域下限",
            horizontal_alignment="center",
            width=0.45
        ),
        ObjectColumn(
            name="upper",
            label=u"区域上限",
            horizontal_alignment="center",
            width=0.45
        ),
    ],
    editable=True,
    deletable=True,
    sortable=False,
    auto_size=True,
    # selection_mode = 'rows',
    # sort_model=True,
    # filters=filters,
    # search=RuleTableFilter(),
    row_factory=RangeModel,
    show_toolbar=True,
    rows=3
)


class FilterView(HasTraits):
    plot_data = Instance(ArrayPlotData)

    signal_plot = Instance(Plot)
    spectrum_plot = Instance(Plot)
    plot = Instance(VPlotContainer)

    selected_ranges = List(RangeModel)
    range_selector = Instance(RangeController)

    bt_import = Button(u'导入')
    bt_export = Button(u'导出')

    view = View(
        VGroup(
            HGroup(
                Item('bt_import', label=' '),
                Item('bt_export', label=' '),
                show_left=False),
            Item('plot', editor=ComponentEditor(size=(600, 600)), show_label=False),
            Item('selected_ranges', editor=table_editor, style='custom', show_label=False, )
        ),
        width=600,
        height=800,
        resizable=False,
        title=u'FFT 过滤'
    )

    def __init__(self, **traits):
        super(FilterView, self).__init__(**traits)
        self.selected_ranges = []
        self.original_signal = None

    def config_signal_view(self, signal_data, x_value, y_value):
        self.original_signal = signal_data

        self.plot_data = ArrayPlotData(
            time=signal_data[x_value],
            original=signal_data[y_value],
            filtered=signal_data[y_value])
        self.signal_plot = Plot(self.plot_data, title='Signal Time History')
        self.signal_plot.plot(('time', 'filtered'), name='filtered', color='red')
        self.signal_plot.plot(('time', 'original'), name='original', color='blue')

        self.signal_plot.legend.visible = True
        self.signal_plot.legend.tools.append(
            LegendHighlighter(component=self.signal_plot.legend)
        )
        add_default_axes(self.signal_plot, "normal", 'Value', 'Time')

    def config_spectrum_view(self, spectrum_data, x_value, y_value):
        plot_data = ArrayPlotData(x=spectrum_data[x_value], y=spectrum_data[y_value])
        self.spectrum_plot = Plot(data=plot_data, title='FFT Spectrum')
        self.spectrum_plot.plot(("x", "y"), type="line", color='black')
        add_default_axes(self.spectrum_plot, "normal", 'Amplitude', 'Frequency')

    def config_main_view(self, graphics_size_x, graphics_size_y):
        self.plot = VPlotContainer(self.spectrum_plot, self.signal_plot)
        self.plot.fixed_preferred_size = (graphics_size_x, graphics_size_y)
        self.range_selector = self.setup_range_selector(self.spectrum_plot.components[0], 1)

    def setup_range_selector(self, curve, addevent):

        # overlay = RangeOverlay(
        #         component=curve, 
        #         # rangedata=RangeModel(low=selector.selection[0], high=selector.selection[1]),
        #         main=self 
        #         )

        # "hub" object which groups both the screen overlay and the data recor for range:
        selector = RangeController(
            curve,
            left_button_selects=True,
            enable_resize=True,
            rangeslist=self.selected_ranges,
            overlayslist=curve.overlays
        )

        if addevent:
            selector.on_trait_change(self.selected_range_changed, "selection")
            selector.on_trait_change(self.selected_range_completed, "event_state")

        # # deactivate another rnges:
        # for rangedata in curve.tools:
        #     if isinstance(rangedata, RangeController):
        #         rangedata.focused = False
        # for overlay in curve.overlays:
        #     if isinstance(overlay, RangeOverlay):
        #         overlay.focused = False;

        curve.tools.append(selector)
        # curve.tools.append(SelectTool(curve))
        # curve.active_tool = selector
        # curve.overlays.append(overlay)
        return selector

    def selected_range_changed(self):
        """ invoked when the range selected by range_selector changed, it changes
        the zoom_plotter's bounds to zoom in the selected range of the plot.
        """
        selection = self.range_selector.selection

        if selection is not None:
            # stop_band = [(selection[0], selection[1])]

            # selected_ranges
            self.pre_selection = RangeModel(lower=selection[0], upper=selection[1])
            # print "calling RangeSelection_1?????????????????????????????????????????????????????"
            # print 'selection: ', str(self.pre_selection)
            # else:
            # self.zoom_plotter.index_range.reset()

    def selected_range_completed(self):
        """
        put selected range into selected_ranges, create a RangeSelectionOverlay
        and append it into curve's overlays.
        """
        # print self.range_selector.event_state
        if self.range_selector.event_state == "normal":  # and self.pre_selection is not None:
            # check if exists:
            # item_found = None
            # for sel_ in self.selected_ranges:
            #     if self.range_selector.rangedata._counter == sel_._counter:
            #         item_found = sel_
            #         sel_.lower = self.range_selector.rangedata.lower
            #         sel_.upper = self.range_selector.rangedata.upper
            #         print "Applying to existed: ", sel_._counter
            #         break
            # if not item_found:
            #     print 'Now appending...'
            #     # self.selected_ranges.append(self.range_selector.rangedata)

            # self.curve_spectrum.overlays.append(
            #     # RangeSelectionOverlay1(
            #     RangeOverlay(
            #         component=self.curve_spectrum,
            #         rangedata=self.pre_selection,
            #         main=self
            #     )
            # )

            self.redraw_signal_plot()

    def redraw_signal_plot(self):
        stop_points = [(range.lower, range.upper) for range in self.selected_ranges if range.active]
        self.plot_data['filtered'] = fil.fft_filter(self.original_signal, stop_points)
        self.signal_plot.request_redraw()


class FilterController(object):
    graphics_size_x = 350
    graphics_size_y = 350

    def __init__(self, signal_data):
        # generate spectrum data from signal data
        spectrum_data = fil.frequency_spectrum(signal_data)

        # define the figure
        self.figure = FilterView()
        self.figure.config_signal_view(signal_data, 'time', 'data')
        self.figure.config_spectrum_view(spectrum_data, 'freqs', 'amplitude')
        self.figure.config_main_view(self.graphics_size_x, self.graphics_size_y)


if __name__ == '__main__':

    filter_controller = FilterController(fil.simulate_signal())
    filter_controller.figure.configure_traits()
