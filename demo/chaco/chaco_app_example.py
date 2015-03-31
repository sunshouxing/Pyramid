# -*- coding: utf-8 -*-

import numpy as np
from traits.api import HasTraits, Instance, Color
from traits.trait_types import Float
from traitsui.api import View, Item, VGroup
from enable.component_editor import ComponentEditor
from chaco.api import Plot, ArrayPlotData, marker_trait


class ScatterPlotTraits(HasTraits):
    plot = Instance(Plot)
    data = Instance(ArrayPlotData)
    color = Color("blue")
    marker = marker_trait
    size = Float

    traits_view = View(
        VGroup(
            Item("color", label="Color"),
            Item("marker", label="Marker"),
            Item("size", label="Size"),
            Item("plot", editor=ComponentEditor(), show_label=False),
        ),
        width=800, height=600, resizable=True, title="Chaco Plot"
    )

    def __init__(self, **traits):
        super(ScatterPlotTraits, self).__init__(**traits)
        x = np.linspace(-14, 14, 100)
        y = np.sin(x) * x ** 3
        data = ArrayPlotData(x=x, y=y)
        plot = Plot(data)
        self.line = plot.plot(("x", "y"), type="scatter", color="blue")[0]
        self.plot = plot
        self.data = data

    def _color_changed(self):
        self.line.color = self.color

    def _marker_changed(self):
        self.line.marker = self.marker

    def _size_changed(self):
        self.line.marker_size = self.size


if __name__ == "__main__":
    p = ScatterPlotTraits()
    p.configure_traits()
