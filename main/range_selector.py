# -*- coding: utf-8 -*-

r"""float range selector"""

# ---- Imports ---------------------------------------------------------------------------
from traits.api import HasTraits
from traits.trait_types import Str, Float, Range
from traitsui.api import View, Item, HGroup


class RangeSelector(HasTraits):
    # ---- Trait Definitions -------------------------------------------------------------
    name = Str("")

    # the lower bound of the value
    lower = Float(0.0)

    # the upper bound of the value
    upper = Float(10.0)

    # the value to select
    value = Range(low="lower", high="upper", value=1.0)

    # ---- Traits View Definitions -------------------------------------------------------
    traits_view = View(
        HGroup(
            Item("name", style="readonly", width=0.1, show_label=False),
            Item("_"),
            Item("lower", label=u"下限", width=0.2),
            Item("value", show_label=False, width=0.5),
            Item("upper", label=u"上限", width=0.2),
            show_border=True,
            enabled_when="name != ''",
        )
    )
