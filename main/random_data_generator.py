# -*- coding: utf-8 -*-

r""" Random data array generator """

# --------[import]-----------------------------------------------------------------------
import numpy as np
from scipy import stats
from traits.api import HasTraits, Instance, Int
from traits.has_traits import on_trait_change
from traitsui.api import View, Item, VGroup, HGroup, spring
from traitsui.editors import EnumEditor
from traitsui.handler import Controller
from traitsui.menu import Action
from chaco.plot import Plot
from chaco.array_plot_data import ArrayPlotData
from enable.component_editor import ComponentEditor

from range_selector import RangeSelector
from workspace import SAMPLES


class GeneratorHandler(Controller):
    plot = Instance(Plot, ())

    resample = Action(
        id="rdg_resample_button_id",
        name=u"重新取样",
        action="do_resample",
    )

    export = Action(
        id="rdg_export_button_id",
        name=u"导出",
        action="do_export",
    )

    def __init__(self):
        pass

    def object_samples_changed(self, info):
        y, x = np.histogram(info.object.samples, bins=100)
        x = (x[:-1] + x[1:]) / 2

        width = (np.max(x) - np.min(x)) / 100

        data = ArrayPlotData(x=x, y=y)
        plot = Plot(data)
        plot.plot(("x", "y"), type="bar", bar_width=width, color="auto")

        self.plot = plot

    def do_resample(self):
        self.model.generate()

    def do_export(self, info):
        data_name = "{}rd_{}".format(info.object.distribution.name, len(SAMPLES))
        SAMPLES[data_name] = self.model.samples.copy()

        info.ui.control.close()


class RandomDataGenerator(HasTraits):
    #--- Trait Definitions-------------------------------------------------------

    # the model of random data distribution
    distribution = Instance(stats.rv_continuous)

    # the location parameter of distribution
    location = Int

    # the scale parameter of distribution
    scale = Int

    # the size of samples
    size = Int

    # the samples
    samples = Instance(np.ndarray)

    # the shape parameters of selected distribution
    sp1 = Instance(RangeSelector, ())
    sp2 = Instance(RangeSelector, ())
    sp3 = Instance(RangeSelector, ())

    #initialization
    def __init__(self, *args, **traits):
        super(RandomDataGenerator, self).__init__(*args, **traits)

        self.distribution = stats.distributions.norm
        self.size = 1000
        self.location = 0
        self.scale = 1


    #-- Event Handlers ---------------------------------------------------------
    def _distribution_changed(self):
        shapes = []

        if self.distribution.shapes is not None:
            shapes = [s.strip() for s in self.distribution.shapes.split(",")]
        while len(shapes) < 3:
            shapes.append("")

        self.sp1, self.sp2, self.sp3 = [RangeSelector(name=label) for label in shapes]

    @on_trait_change("distribution,location,scale,size,sp1.value,sp2.value,sp3.value")
    def generate(self):
        try:
            shapes = {p.name: p.value for p in [self.sp1, self.sp2, self.sp3] if p.name != ""}
            distribution = self.distribution(loc=self.location, scale=self.scale, **shapes)
            self.samples = distribution.rvs(size=self.size)
        except Exception as error:
            print "shape parameters: {}".format(error)

    #--- Traits View Definitions ------------------------------------------------
    traits_view = View(
        VGroup(
            HGroup(
                spring,
                Item(
                    "distribution",
                    editor=EnumEditor(
                        values={v: k for (k, v) in stats.__dict__.items() if isinstance(v, stats.rv_continuous)}
                    ),
                    label=u"分布类型",
                ),
                Item("location", label=u"位置", ),
                Item("scale", label=u"缩放比例"),
                Item("size", label=u"样本数量"),
                spring,
                show_border=True,
            ),
            Item("handler.plot", style="custom", show_label=False, editor=ComponentEditor()),
            VGroup(
                Item("sp1", style="custom", show_label=False),
                Item("sp2", style="custom", show_label=False),
                Item("sp3", style="custom", show_label=False),
                show_border=True,
                label=u"形状参数",
            ),
        ),
        resizable=True,
        kind="livemodal",
        title=u"随机变量生成器",
        handler=GeneratorHandler,
        buttons=[GeneratorHandler.resample, GeneratorHandler.export],
    )

