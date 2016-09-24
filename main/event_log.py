# -*- coding: utf-8 -*-

# ---- Imports -----------------------------------------------------------
from pyface.api import ImageResource
from traits.api import HasTraits, Str, Code, Button
from traitsui.api import \
    View, HGroup, VGroup, UReadonly, UCustom, spring, Controller


class LogModel(HasTraits):
    log = Code

    def write(self, text):
        self.log += text

    def clear(self):
        self.log = ''


class EventLog(Controller):
    name = Str

    clear_button = Button(
        image=ImageResource('../icons/glyphicons-17-bin.png'),
        style='toolbar'
    )

    custom_view = View(
        HGroup(
            VGroup(
                UCustom('handler.clear_button', tooltip=u'清除日志'),
                spring,
            ),
            '_',
            UReadonly('log'),
        ),
    )

    def __init__(self, *args, **traits):
        super(EventLog, self).__init__(*args, **traits)
        self.name = u'系统日志'


if __name__ == '__main__':
    EventLog(model=LogModel()).configure_traits()

# EOF
