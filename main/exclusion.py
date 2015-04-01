# -*- coding: utf-8 -*-

r"""module doc
"""
# ---- Imports ---------------------------------------------------------------------------
from traits.has_traits import HasTraits
from traits.trait_types import Str, Int, Enum
from traitsui.group import VGroup, HGroup
from traitsui.item import Item, spring
from traitsui.view import View


class Exclusion(HasTraits):
    # exclude the item if the function return True
    def exclude(self, item):
        pass


class BasicExclusion(Exclusion):
    name = Str

    lower = Int
    upper = Int

    lower_operator = Enum("<", "<=")
    upper_operator = Enum(">", ">=")

    def _lt(self, item):
        return item < self.lower

    def _le(self, item):
        return item <= self.lower

    def _gt(self, item):
        return item > self.upper

    def _ge(self, item):
        return item >= self.upper

    def exclude(self, item):
        op_map = {"<": self._lt, "<=": self._le, ">": self._gt, ">=": self._ge}
        return op_map[self.lower_operator](item) or op_map[self.upper_operator](item)

    view = View(
        Item("name", label="Exclusion rule name"),
        VGroup(
            HGroup(
                spring,
                Item("lower_operator", label="Lower limit: exclude data"),
                spring,
                Item("lower", show_label=False),
                spring,
            ),
            HGroup(
                spring,
                Item("upper_operator", label="Upper limit: exclude data"),
                spring,
                Item("upper", show_label=False),
                spring,
            ),
            label="Exclude section",
            show_border=True,
        ),
        title="Exclude",
    )


if __name__ == "__main__":
    e = BasicExclusion()
    e.configure_traits()
