# -*- coding: utf-8 -*-

# ---- Imports -----------------------------------------------------------
from traits.api import *
from traitsui.api import *

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('LoggingTest')


class LogModel(HasTraits):
    # log content
    log = Code

    def __init__(self):
        super(LogModel, self).__init__()
        self.log = ''

    def write(self, text):
        self.log += text

logger = LogModel()


class SystemLog(ModelView):

    def __init__(self):
        super(SystemLog, self).__init__()
        self.model = logger

    traits_view = View(
        '10',
        UReadonly('model.log'),
        '10',
    )

# EOF
