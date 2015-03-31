# -*- coding: utf-8 -*-
from traits.api import HasTraits, Instance, List
from traitsui.api import View, Item, TableEditor, ObjectColumn
from traitsui.table_filter import \
    EvalFilterTemplate, MenuFilterTemplate, RuleFilterTemplate
from chaco.api import Plot, ArrayPlotData, VPlotContainer
from chaco.tools.api import RangeSelection as RangeSelector
from chaco.tools.api import RangeSelectionOverlay as RangeSelectorOverlay
from enable.component_editor import ComponentEditor
import numpy as np

from range_selection import RangeSelectionOverlay, RangeSelection


def generate_simulate_data():
    """ Generate simulate data for this demo """
    x = np.linspace(-140, 140, 500)
    y = np.sin(x) * x ** 3
    y /= np.max(y)

    return ArrayPlotData(x=x, y=y)


filters = [EvalFilterTemplate, MenuFilterTemplate, RuleFilterTemplate]

table_editor = TableEditor(
    columns=[
        ObjectColumn(
            name="active",
            label=u"是否使用",
            horizontal_alignment="center",
            style="custom",
            format_func=lambda b: b and u"是" or u"否",
            width=0.1
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
    # sort_model=True,
    auto_size=True,
    # filters=filters,
    # search=RuleTableFilter(),
    row_factory=RangeSelection,
    show_toolbar=True,
    rows=3,
)


class MultiSelection(HasTraits):
    plot = Instance(VPlotContainer)
    data = Instance(ArrayPlotData)

    selected_ranges = List(RangeSelection)

    traits_view = View(
        Item(
            "plot",
            editor=ComponentEditor(size=(600, 600)),
            show_label=False
        ),
        Item(
            "selected_ranges",
            style="custom",
            editor=table_editor,
            show_label=False,
        ),
        width=600,
        height=800,
        resizable=False,
        title=u"范围选择演示"
    )

    def __init__(self, data, **traits):
        super(MultiSelection, self).__init__(**traits)

        self.pre_selection = None
        self.selected_ranges = []

        # self.data = generate_simulate_data()
        self.data = data

        # create plot main structure
        self.main_plotter = Plot(self.data)
        self.zoom_plotter = Plot(self.data)
        self.plot = VPlotContainer(self.zoom_plotter, self.main_plotter)

        self.plot.fixed_preferred_size = (350, 100)

        # plotting
        self.curve = self.main_plotter.plot(("x", "y"), type="line")[0]
        self.zoom_plotter.plot(("x", "y"), type="line")

        # setup range selector
        self.range_selector = self.setup_range_selector(self.curve)

    def setup_range_selector(self, curve):
        selector = RangeSelector(curve)
        selector.on_trait_change(self.selected_range_changed, "selection")
        selector.on_trait_change(self.selected_range_completed, "event_state")
        curve.tools.append(selector)
        curve.overlays.append(RangeSelectorOverlay(component=curve))

        return selector

    def selected_range_changed(self):
        """ invoked when the range selected by range_selector changed, it changes
        the zoom_plotter's bounds to zoom in the selected range of the plot.
        """
        selection = self.range_selector.selection
        if selection is not None:
            self.zoom_plotter.index_range.set_bounds(*selection)
            self.pre_selection = RangeSelection(*selection)
            # else:
            # self.zoom_plotter.index_range.reset()

    def selected_range_completed(self):
        """ put selected range into selected_ranges, create a RangeSelectionOverlay
        and append it into curve's overlays.
        """
        if self.range_selector.event_state == "normal" and self.pre_selection is not None:
            self.selected_ranges.append(self.pre_selection)
            self.curve.overlays.append(
                RangeSelectionOverlay(
                    component=self.curve,
                    selection=self.pre_selection
                )
            )


if __name__ == "__main__":
    p = MultiSelection()
    p.configure_traits()
