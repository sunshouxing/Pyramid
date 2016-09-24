# -*- coding: utf-8 -*-

# ---- [Imports] --------------------------------------------------------------
from traits.api import SingletonHasTraits, Unicode
from traitsui.api import View, Include, UItem


class MainUIComponent(SingletonHasTraits):
    name = Unicode

    traits_view = View(
        # main ui components' common view item should be added here
        # UItem('name'),
        Include('custom_view'),
    )

    def __int__(self, *args, **traits):
        super(MainUIComponent, self).__int__(*args, **traits)

# EOF
