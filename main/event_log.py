# -*- coding: utf-8 -*-

# ---- Imports -----------------------------------------------------------
from pyface.api import ImageResource
from traits.api import HasTraits, Str, Code, Button
from traitsui.api import \
    View, HGroup, VGroup, UReadonly, UCustom, spring, Controller

from common import ICONS_PATH


class LogModel(HasTraits):
    log = Code

    def write(self, text):
        self.log += text

    def clear(self):
        self.log = ''


class EventLog(Controller):
    tab_name = Str

    clear_button = Button(
        image=ImageResource('glyphicons-17-bin.png', search_path=[ICONS_PATH]),
        style='toolbar'
    )

    custom_view = View(
        HGroup(
            VGroup(
                UCustom('handler.clear_button', tooltip=u'清除日志'),
                spring,
                show_border=True,
            ),
            # '_',
            UReadonly('log'),
        ),
    )

    def __init__(self, *args, **traits):
        super(EventLog, self).__init__(*args, **traits)
        self.tab_name = u'系统日志'


event_log = EventLog(model=LogModel())

if __name__ == '__main__':
    event_log.configure_traits()

# EOF
