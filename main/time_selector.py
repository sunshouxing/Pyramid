# -*- coding: utf-8 -*-

r"""date and time selector"""

# -------[import]-----------------------------------------------------------------
from traits.has_traits import HasTraits
from traits.trait_types import Time, Date
from traitsui.group import HGroup
from traitsui.item import Item
from traitsui.view import View


class TimeSelector(HasTraits):
    #--- Trait Definitions-------------------------------------------------------
    date = Date

    time = Time

    def __init__(self, label=''):
        self.label = label

    #--- Traits View Definitions ------------------------------------------------
    def traits_view(self):
        return View(
            HGroup(
                Item('date', show_label=False),
                Item('time', show_label=False),
                show_border=True,
                label=self.label,
            )
        )