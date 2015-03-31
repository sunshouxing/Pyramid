# -*- coding: utf-8 -*-
from chaco.plot_containers import OverlayPlotContainer
import numpy as np
from traits.api import HasTraits, Instance
from traitsui.api import View, Item
from chaco.api import Plot, ArrayPlotData
from enable.component_editor import ComponentEditor
from chaco.tools.api import RangeSelection, RangeSelectionOverlay


class SelectionDemo(HasTraits):
    plot = Instance(OverlayPlotContainer)
    data = Instance(ArrayPlotData)

    traits_view = View(
        Item(
            'plot',
            editor=ComponentEditor(),
            show_label=False
        ),
        width=500,
        height=500,
        resizable=True,
        title=u"范围选择演示"
    )

    def __init__(self, **traits):
        super(SelectionDemo, self).__init__(**traits)

        x = np.linspace(-140, 140, 1000)
        y = np.sin(x) * x ** 3
        y /= np.max(y)
        data = ArrayPlotData(x=x, y=y)

        main_plotter = Plot(data, padding=25)
        self.line = main_plotter.plot(("x", "y"), type="line")[0]

        self.select_tool = RangeSelection(self.line)
        self.select_tool.on_trait_change(self.selection_changed, "selection")
        self.line.tools.append(self.select_tool)

        self.line.overlays.append(RangeSelectionOverlay(component=self.line))

        zoom_plotter = Plot(data, padding=25)
        zoom_plotter.plot(("x", "y"), type="line")[0]

        self.main_plotter = main_plotter
        self.zoom_plotter = zoom_plotter

        self.plot = OverlayPlotContainer(zoom_plotter, main_plotter)
        self.data = data


    def selection_changed(self):
        selection = self.select_tool.selection
        if selection is not None:
            self.zoom_plotter.index_range.set_bounds(*selection)
        else:
            self.zoom_plotter.index_range.reset()


if __name__ == "__main__":
    p = SelectionDemo()
    p.configure_traits()