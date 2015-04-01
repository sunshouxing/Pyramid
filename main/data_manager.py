# -*- coding: utf-8 -*-

r""" Used by distribution fitting tool to import data or generate random data """

# ---- Imports ---------------------------------------------------------------------------
import numpy as np
from traits.api import HasTraits, Instance
from traits.trait_types import Str, List, Bool
from traitsui.api import View, Item, HGroup, VGroup, Group
from traitsui.editors import EnumEditor
from traitsui.handler import Controller
from traitsui.menu import Action
from chaco.api import Plot, ArrayPlotData
from enable.component_editor import ComponentEditor

from workspace import DATA


class DataManager(Controller):
    # all the keys of DATA
    candidate_data_names = List(Str)

    # the select key of DATA
    selected_data_name = Str

    # data to plot
    data = Instance(ArrayPlotData)

    plot = Instance(Plot)

    def __init__(self):
        self.candidate_data_names = DATA.keys()
        self.data = ArrayPlotData()
        self.plot = Plot(self.data)

    def _selected_data_name_changed(self):
        self.info.object.data = DATA[self.selected_data_name]

        y, x = np.histogram(self.info.object.data, bins=50)
        x = (x[:-1] + x[1:]) / 2
        self.data["x"] = x
        self.data["y"] = y

        width = np.ptp(x) / 50
        self.plot.plot(("x", "y"), type="bar", bar_width=width, color="auto")

    def generate_random_data(self, info):
        from random_data_generator import RandomDataGenerator

        generator = RandomDataGenerator()
        generator.edit_traits()

        self.candidate_data_names = DATA.keys()

    def complete(self, info):
        """the real action of Complete Button"""
        DATA[info.object.name] = self.model.data
        self.model.target.current_data_name = self.model.name
        info.ui.control.close()


class DataImporter(HasTraits):
    # ---- Trait Definitions -------------------------------------------------------------
    data = Instance(np.ndarray)

    name = Str

    completable = Bool

    def __init__(self, target):
        self.target = target

    def _data_changed(self):
        self.is_completable()

    def _name_changed(self):
        self.is_completable()

    def is_completable(self):
        if self.data is not None and self.name != "":
            self.completable = True
        else:
            self.completable = False

    # ---- Traits View Definitions -------------------------------------------------------
    complete_button = Action(
        id="dm_complete_button",
        name=u"完成",
        action="complete",
        enabled_when="completable",
    )

    generate_random_data_button = Action(
        id="dm_generate_random_data_button",
        name=u"生成模拟数据...",
        action="generate_random_data",
    )

    trait_view = View(
        HGroup(
            VGroup(
                Item(
                    "handler.selected_data_name",
                    editor=EnumEditor(name="handler.candidate_data_names"),
                    label=u"数据集",
                ),
                Item("name", label=u"名称"),
            ),
            Item("_"),
            Group(
                Item("handler.plot", editor=ComponentEditor(), show_label=False),
                label=u"数据预览",
                show_border=True,
            ),
        ),
        handler=DataManager,
        buttons=[generate_random_data_button, complete_button],
    )
