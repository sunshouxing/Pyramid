# -*- coding: utf-8 -*-

# ---- Imports ---------------------------------------------------------------------------
import numpy as np
from scipy import stats
from scipy.stats import rv_continuous

from traits.api import \
    HasTraits, Bool, Str, Any, Instance, Float, List, Button, DelegatesTo
from traitsui.api import \
    View, Controller, Item, UItem, UReadonly, Action, \
    Group, VGroup, HGroup, spring, EnumEditor

from main.workspace import workspace


class FitGenerator(Controller):
    # ---- Trait Definitions -------------------------------------------------------------

    # names of all data in data space
    candidate_data_names = List(Str)

    # the name of selected data
    selected_data_name = Str

    # the data selected to fit with
    data = Instance(np.ndarray)

    # fitter toolkit
    target = Any

    apply_fit_button = Button(u'应用')

    export_fit_button = Action(
        id="fit_export_fit_id",
        name=u"导出至工作区",
        action="export_fit",
    )

    def __init__(self, target, **traits):
        super(FitGenerator, self).__init__(**traits)
        self.target = target
        self.candidate_data_names = workspace.data.keys()

    # ---- Event Handlers ----------------------------------------------------------------
    def _selected_data_name_changed(self):
        self.data = workspace.data[self.selected_data_name]

    def _apply_fit_button_fired(self):
        params = self.model.distribution.fit(self.data)

        self.model.loc = loc = params[-2]
        self.model.scale = scale = params[-1]

        shapes = {s: p for s, p in zip(self.info.object.shapes, params)}
        self.model.shapes_desc = '\n'.join(['{} = {}'.format(k, v) for k, v in shapes.items()])

        shapes.update({'loc': loc, 'scale': scale})
        self.model.desc = '\n'.join(['{} = {}'.format(k, v) for k, v in shapes.items()])
        self.info.object.fit = self.model.distribution(**shapes)

    def export_fit(self, info):
        from toolbox.fitter.fit_manager import FitManager

        workspace.fits[self.model.name] = self.model.fit
        self.target.current_fit_name = self.model.name

        fit_manager = FitManager()
        fit_manager.model.fits.append(self.model)

        info.ui.control.close()

    # ---- Traits View Definitions -------------------------------------------------------
    traits_view = View(
        VGroup(
            Group(
                Item("name", label=u"拟合名称", width=200),
                Item(
                    "handler.selected_data_name",
                    editor=EnumEditor(name="handler.candidate_data_names"),
                    label=u"拟合数据",
                    width=200,
                ),
                Item(
                    "distribution",
                    editor=EnumEditor(
                        values={v: k for (k, v) in stats.__dict__.items() if isinstance(v, stats.rv_continuous)}
                    ),
                    label=u"拟合函数",
                    width=200,
                ),
            ),
            Group(
                UReadonly("shapes"), label=u"拟合函数参数表", show_border=True,
            ),
            HGroup(
                spring, UItem("handler.apply_fit_button"),
            ),
            Group(
                UItem("desc", style="custom"), label=u"拟合结果",
            ),
        ),
        buttons=[export_fit_button],
        title=u"数据拟合窗口",
        height=700,
        width=400,
        resizable=True,
    )


class Fit(HasTraits):
    # ---- Trait Definitions -------------------------------------------------------------

    # the fit's name
    name = Str

    # the distribution type
    distribution = Instance(rv_continuous)

    # fit's distribution type
    type = Str

    # the fit's location parameter
    loc = Float

    # the fit's scale parameter
    scale = Float

    # the fit's specific shape parameters
    shapes = List(Str)

    # the fit shapes' string format description
    shapes_desc = Str

    # fit's description including shapes, loc, scale
    desc = Str

    # flag for management
    selected = Bool(False)

    # - Event Handlers ---------------------------------------------------------
    def _distribution_changed(self):
        self.type = self.distribution.name

        if self.distribution is not None and self.distribution.shapes is not None:
            self.shapes = [p.strip() for p in self.distribution.shapes.split(",")]
        else:
            self.shapes = []

# EOF
