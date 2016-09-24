# -*- coding: utf-8 -*-

# ---- Imports -----------------------------------------------------------
from pyface.api import ImageResource
from traits.api import HasTraits, Unicode, Str
from traitsui.api import View, Include, UItem


class MainUIComponent(HasTraits):
    name = Unicode

    traits_view = View(
        UItem('name'),
        Include('custom_view'),
        icon=ImageResource('../icons/glyphicons-120-table.png'),
    )

    def __int__(self, *args, **traits):
        super(MainUIComponent, self).__int__(*args, **traits)

# EOF
