# -*- coding: utf-8 -*-

""" The global workspace environment
"""

# ---- Import -------------------------------------------------------------
from traits.api import *


class Workspace(SingletonHasTraits):

    data = Dict

    fits = Dict


workspace = Workspace()

# EOF
