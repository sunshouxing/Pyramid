# -*- coding: utf-8 -*-

r"""module doc
"""
# ------[import]-----------------------------------------------------------------------
import numpy as np
from scipy import stats
from scipy.stats import rv_continuous
from traits.api import HasTraits, Instance, Str
from traits.trait_types import List, Button
from traitsui.api import View, Item, Group
from traitsui.editors import EnumEditor
from traitsui.group import VGroup, HGroup
from traitsui.handler import Controller
from traitsui.item import spring, Label
from traitsui.menu import Action

from workspace import FITS
from workspace import DATA


class FitController(Controller):
    # --- Trait Definitions-------------------------------------------------------
    candidate_data_names = List(Str)
    selected_data_name = Str
    fit_result = Str
    apply_fit_button = Button(u"应用")

    export_fit_button = Action(
        id="fit_export_fit_id",
        name=u"导出至工作区",
        action="export_fit",
    )

    def __init__(self):
        self.candidate_data_names = DATA.keys()

    # -- Event Handlers ----------------------------------------------------------
    def _selected_data_name_changed(self):
        self.info.object.data = DATA[self.selected_data_name]

    def _apply_fit_button_fired(self):
        distribution = self.info.object.distribution
        data = self.info.object.data
        params = distribution.fit(data)
        shapes = {s: p for s, p in zip(self.info.object.shapes, params)}
        shapes["loc"] = params[-2]
        shapes["scale"] = params[-1]

        self.info.object.fit = self.info.object.distribution(**shapes)

    def export_fit(self, info):
        fit_name = self.model.name
        fit = info.object.fit
        FITS[fit_name] = fit

        self.model.target.current_fit_name = info.object.name
        info.ui.control.Close()


class Fit(HasTraits):
    # ---- Trait Definitions-------------------------------------------------------
    # the fit's name
    name = Str

    # the data to fit with
    data = Instance(np.ndarray)

    # the distribution type
    distribution = Instance(rv_continuous)

    # the distribution's shape parameters
    shapes = List(Str)

    def __init__(self, target):
        self.target = target

    #-- Event Handlers ---------------------------------------------------------
    def _distribution_changed(self):
        if self.distribution is not None and self.distribution.shapes is not None:
            self.shapes = [p.strip() for p in self.distribution.shapes.split(",")]
        else:
            self.shapes = []

    #---- Traits View Definitions ------------------------------------------------
    traits_view = View(
        VGroup(
            Group(
                Item("name", label=u"拟合名称"),
                Item(
                    "handler.selected_data_name",
                    editor=EnumEditor(name="handler.candidate_data_names"),
                    label=u"拟合数据",
                ),
                Item(
                    "distribution",
                    editor=EnumEditor(
                        values={v: k for (k, v) in stats.__dict__.items() if isinstance(v, stats.rv_continuous)}
                    ),
                    label=u"拟合函数",
                ),
            ),
            Group(
                Item("shapes", style="readonly", show_label=False),
                label=u"拟合函数参数表",
                show_border=True,
            ),
            HGroup(
                spring, Item("handler.apply_fit_button", show_label=False),
            ),
            Group(
                Label(u"拟合结果"),
                Item("handler.fit_result", style="custom", show_label=False),
            ),
        ),
        handler=FitController,
        buttons=[FitController.export_fit_button],
        height=700,
        width=400,
        resizable=True,
    )
