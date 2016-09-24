# -*- coding: utf-8 -*-

"""
Functions and classes for common use.
"""

# ---- Imports -----------------------------------------------------------
from os import path

# the project's home directory
PROJECT_HOME = path.dirname(__file__)

# the icons' storage path
ICONS_PATH = path.join(PROJECT_HOME, 'icons')

# the bridges' description file storage path
BRIDGES_PATH = path.join(PROJECT_HOME, 'bridges')

# directory where binary tools locate
BINARY_PATH = path.join(PROJECT_HOME, 'binary')

# logs directory
LOG_PATH = path.join(PROJECT_HOME, 'logs')


def singleton(cls):
    """
    A decorator to make the decorated *cls* have only one instance.

    Example:

    @singleton
    class Foo(object):
        pass

    :param cls: class
        The class to be decorated
    :return:
        The decorated class
    """
    _instances = {}

    def _singleton(*args, **traits):
        if cls not in _instances:
            _instances[cls] = cls(*args, **traits)
        return _instances[cls]

    return _singleton

# EOF

