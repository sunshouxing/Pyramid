# -*- coding: utf-8 -*-

r"""distribution fitting tool"""

# ---- Imports ---------------------------------------------------------------------------
import numpy as np
from traits.api import HasTraits, Instance, Enum, Button, Dict
from traits.has_traits import on_trait_change
from traits.trait_types import Str
from traitsui.api import View, Item, UItem, HGroup, VGroup, spring, Group
from traitsui.editors import ShellEditor
from traitsui.handler import Controller
from traitsui.menu import Action, ActionGroup, Menu, MenuBar, ToolBar
from pyface.image_resource import ImageResource
from chaco.api import Plot, ArrayPlotData
from enable.component_editor import ComponentEditor

from main.workspace import DATA
from main.workspace import FITS


class DistributionFittingToolController(Controller):
    config_data_button = Button(u"数据...")
    new_fit_button = Button(u"新拟合...")
    manage_fits_button = Button(u"拟合管理...")
    evaluate_button = Button(u"评估...")
    exclude_data_button = Button(u"例外...")

    def _config_data_button_fired(self):
        from toolbox.common import Data, DataManager
        data = Data(self.info.object)
        data_manager = DataManager(data)
        data_manager.edit_traits()

    def _new_fit_button_fired(self):
        from fit import Fit

        fit = Fit(target=self.info.object)
        fit.edit_traits()


class DistributionFittingTool(HasTraits):
    values = Dict

    # plot data
    data = Instance(ArrayPlotData)

    # plot to show fit effect
    plot = Instance(Plot)

    # current fit's name
    current_fit_name = Str

    # current data's name
    current_data_name = Str

    display_type = Enum(
        "Density(PDF)",
        "Cumulative Probability(CDF)",
        "Quality(inverse CDF)",
        "Probability Plot",
        "Survival function",
        "Cumulative hazard"
    )

    distribution = Enum(
        "Normal",
        "Lognormal"
    )

    def __init__(self, *args, **traits):
        super(DistributionFittingTool, self).__init__(*args, **traits)
        self.data = ArrayPlotData()
        self.plot = Plot(self.data)

    @on_trait_change("current_data_name")
    def data_changed(self):
        data = DATA[self.current_data_name]
        y, x = np.histogram(data, bins=100, normed=True)
        x = (x[:-1] + x[1:]) / 2

        self.data["x"] = x
        self.data["y"] = y

        plot = Plot(self.data)

        width = np.ptp(x) / 100
        bar_plot = plot.plot(("x", "y"), type="bar", name=self.current_data_name, bar_width=width, color="auto")[0]
        bar_plot.fill_color = bar_plot.fill_color_[:3] + (0,)

        plot.legend.visible = True

        self.plot = plot

    @on_trait_change("current_fit_name")
    def fit_changed(self):
        fit = FITS[self.current_fit_name]

        x = self.data["x"]
        z = fit.pdf(x)
        self.data["z"] = z

        plot = Plot(self.data)
        plot.plot(("x", "z"), type="line", name=self.current_fit_name, color="blue")

        width = np.ptp(x) / 100
        bar_plot = plot.plot(("x", "y"), type="bar", name=self.current_data_name, bar_width=width, color="auto")[0]
        bar_plot.fill_color = bar_plot.fill_color_[:3] + (0,)

        plot.legend.visible = True

        self.plot = plot

    # ------------------------------------------------------------------------------------
    # design the view of distribution fitting tool
    # ------------------------------------------------------------------------------------
    @staticmethod
    def traits_view():
        # design menu
        menu_bar = MenuBar(
            Menu(
                ActionGroup(
                    Action(id="import_data", name="Import Data...", action="import_data"),
                ),
                ActionGroup(
                    Action(id="clear_session", name="Clear Session", action="clear_session"),
                    Action(id="load_session", name="Load Session...", action="load_session"),
                    Action(id="save_session", name="Save Session...", action="save_session"),
                    Action(id="generate_code", name="Generate Code...", action="generate_code"),
                ),
                name="File"
            ),

            Menu(
                name="View"
            ),

            Menu(
                name="Tool"
            ),

            Menu(
                name="Window"
            ),

            Menu(
                ActionGroup(
                    Action(id="help", name="Statistics Toolbox Help", action="about_dialog"),
                    Action(id="help1", name="Distribution Fitting Tool Help", action="about_dialog"),
                ),
                ActionGroup(
                    Action(id="help2", name="Demos", action="about_dialog"),
                ),
                name="Help"
            )
        )

        # design tool bar
        tool_bar = ToolBar(
            Action(
                image=ImageResource("folder_page.png", search_path=["img"]),
                tooltip="Print Figure",
                action="print_figure"
            ),
            Action(
                image=ImageResource("disk.png", search_path=["img"]),
                tooltip="Zoom In",
                action="zoom_in"
            ),
            Action(
                image=ImageResource("disk.png", search_path=["img"]),
                tooltip="Zoom Out",
                action="zoom_out"
            ),
            Action(
                image=ImageResource("disk.png", search_path=["img"]),
                tooltip="Pan",
                action="pan"
            ),
            Action(
                image=ImageResource("disk.png", search_path=["img"]),
                tooltip="Legend On/Off",
                action="zoom_out"
            ),
            Action(
                image=ImageResource("disk.png", search_path=["img"]),
                tooltip="Grid On/Off",
                action="zoom_out"
            ),
            Action(
                image=ImageResource("disk.png", search_path=["img"]),
                tooltip="Restore Default Axes Limits",
                action="zoom_out"
            ),
        )

        return View(
            VGroup(
                HGroup(
                    Item("display_type", width=150),
                    Item("distribution", width=150),
                    show_border=True,
                ),
                HGroup(
                    spring,
                    UItem("handler.config_data_button", tooltip="Import, view, rename, plot and delete data"),
                    UItem("handler.new_fit_button", tooltip="Add a fitted distribution"),
                    UItem("handler.manage_fits_button", tooltip="Edit, view, plot and rename fits"),
                    UItem("handler.evaluate_button", tooltip="Evaluate fits to compute a table of results"),
                    UItem("handler.exclude_data_button", tooltip="Define rules for excluding data from a fit"),
                    spring,
                ),
                UItem("plot", editor=ComponentEditor()),
                label="Manager",
            ),
            Group(
                UItem(
                    "values",
                    editor=ShellEditor(share=True),
                    dock="tab",
                    export="DockWindowShell",
                ),
                label="Console",
            ),
            menubar=menu_bar,
            toolbar=tool_bar,
            resizable=True,
            width=1200, height=700,
            title=u"分布拟合工具箱",
            handler=DistributionFittingToolController(),
        )


if __name__ == "__main__":
    tool = DistributionFittingTool()
    tool.configure_traits()
