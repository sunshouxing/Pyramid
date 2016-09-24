# -*- coding: utf-8 -*-

""" The global workspace environment
"""

# ---- Import -------------------------------------------------------------
# from traits.api import HasTraits, Dict, List
# from common import singleton
#
# @singleton
# class Workspace(HasTraits):
#     data = Dict
#     fits = List


def get_data():
    return get_data.data

def get_fits():
    return get_fits.fits

get_data.data = {}

get_fits.fits = {}

# EOF
