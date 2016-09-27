# -*- coding: utf-8 -*-

""" The global workspace environment
"""

# ---- Import -------------------------------------------------------------
from traits.api import *


class Workspace(SingletonHasTraits):

    data_space = Dict


workspace = Workspace()

# EOF
