# -*- coding: utf-8 -*-

r""" Used by distribution fitting tool to import data or generate random data """

# ---- Imports ---------------------------------------------------------------------------
from traits.api \
    import HasTraits, Str, Instance, Property, Button, List, cached_property
from traitsui.api \
    import View, Item, UItem, HGroup, VGroup, Controller, Action, EnumEditor, spring
from chaco.api import Plot, ArrayPlotData
from enable.api import ComponentEditor

import numpy as np
from main.workspace import DATA


class DataManager(Controller):
    # all the keys of DATA
    candidate_data_names = List(Str)

    # the select key of DATA
    selected_data_name = Str

    # selected data distribution preview plot
    plot = Instance(Plot)

    # button to generate new random variables
    new_data_button = Button

    completable = Property(depends_on=['selected_data_name'])

    def __init__(self, *args, **traits):
        super(DataManager, self).__init__(*args, **traits)

        self.candidate_data_names = DATA.keys()
        self.plot = Plot(ArrayPlotData(), title='Data Preview')

    def _selected_data_name_changed(self):
        if self.selected_data_name not in DATA.keys():
            return

        self.model.data = DATA[self.selected_data_name]

        y, x = np.histogram(self.info.object.data, bins=50)
        x = (x[:-1] + x[1:]) / 2
        self.plot.data["x"] = x
        self.plot.data["y"] = y

        width = np.ptp(x) / 50
        self.plot.plot(("x", "y"), type="bar", bar_width=width, color="auto")

    def _new_data_button_fired(self, info):
        from ..generator.random_data_generator import RandomDataGenerator, RandomData
        RandomDataGenerator(RandomData()).edit_traits()

        self.candidate_data_names = DATA.keys()

    @cached_property
    def _get_completable(self):
        return self.selected_data_name is not None

    def complete(self, info):
        """the real action of Complete Button"""
        self.model.demander.current_data_name = self.selected_data_name
        info.ui.control.close()

    # ---- Traits View Definitions -------------------------------------------------------
    complete_button = Action(
        id="dm_complete_button",
        name=u"完成",
        action="complete",
        enabled_when="handler.completable",
    )

    trait_view = View(
        VGroup(
            HGroup(
                Item('10'),
                Item(
                    "handler.selected_data_name",
                    editor=EnumEditor(name="handler.candidate_data_names", cols=20),
                    label=u"数据集", width=200,
                ),
                spring,
                UItem('handler.new_data_button', label=u"生成数据..."),
                Item('10'),
            ),
            Item('10'),
            UItem("handler.plot", editor=ComponentEditor()),
        ),
        buttons=[complete_button],
        title=u"数据预览窗口",
        resizable=True,
        kind='live'
    )


class Data(HasTraits):
    # ---- Trait Definitions -------------------------------------------------------------
    data = Instance(np.ndarray)

    def __init__(self, demander, **traits):
        super(Data, self).__init__(**traits)
        # demander is the toolkit which is required to process this data
        self.demander = demander
