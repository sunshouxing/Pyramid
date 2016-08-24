# -*- coding: utf-8 -*-

r""" Random data array generator """

# ---- Imports ---------------------------------------------------------------------------
from scipy import stats
import numpy as np

from traits.api \
    import HasTraits, Instance, Int, Str, on_trait_change
from traitsui.api import \
    View, Item, UItem, UCustom, VGroup, HGroup, spring, EnumEditor, Controller, Action, OKButton
from chaco.api import Plot, ArrayPlotData
from enable.api import ComponentEditor

from ..common.range_selector import RangeSelector
from main.workspace import DATA


class RandomDataGenerator(Controller):
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

    def object_samples_changed(self, info):
        y, x = np.histogram(info.object.samples, bins=100)
        x = (x[:-1] + x[1:]) / 2

        width = (np.max(x) - np.min(x)) / 100

        data = ArrayPlotData(x=x, y=y)
        plot = Plot(data)
        plot.plot(("x", "y"), type="bar", bar_width=width, color="auto")

        self.plot = plot

    def do_resample(self, info):
        self.model.generate()

    def do_export(self, info):
        self.edit_traits(view=View(
            HGroup(
                spring,
                UItem('samples_name', tooltip=u'请为导出数据选择一个合适的名字,并保证该名字未被以存在数据占用'),
                spring
            ),
            buttons=[OKButton],
            title=u'数据命名',
            width=250,
        ), kind='livemodal')
        DATA[self.model.samples_name] = self.model.samples
        # close the random data generator window after data exported
        info.ui.control.close()

    # ---- Traits View Definitions -------------------------------------------------------
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
            UCustom("handler.plot", editor=ComponentEditor()),
            VGroup(
                UItem("sp1", style="custom"),
                UItem("sp2", style="custom"),
                UItem("sp3", style="custom"),
                show_border=True,
                label=u"形状参数",
            ),
        ),
        resizable=True,
        kind="livemodal",
        title=u"随机变量生成器",
        buttons=[resample, export],
    )


class RandomData(HasTraits):
    # ---- Trait Definitions -------------------------------------------------------------

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

    # the samples' name
    samples_name = Str

    # the shape parameters of selected distribution
    sp1 = Instance(RangeSelector, ())
    sp2 = Instance(RangeSelector, ())
    sp3 = Instance(RangeSelector, ())

    # initialization
    def __init__(self, *args, **traits):
        super(RandomData, self).__init__(*args, **traits)

        self.distribution = stats.distributions.norm
        self.size = 1000
        self.location = 0
        self.scale = 1

    # - Event Handlers ---------------------------------------------------------
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


if __name__ == '__main__':
    generator = RandomDataGenerator(RandomData())
    generator.configure_traits()
