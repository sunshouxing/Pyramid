# -*- coding: utf-8 -*-

# ---- Imports -----------------------------------------------------------
import numpy as np


def has_items(data):
    """ does data have child items
    """
    return hasattr(data, '__iter__') and not isinstance(data, str)


def is_sequence(data):
    """ is data like array
    """
    return has_items(data) and not isinstance(data, dict)


def is_mutable_sequence(data):
    """ is data a mutable array
    """
    return is_sequence(data) and hasattr(data, '__setitem__')


def is_matrix(data):
    """ is data a matrix
    """
    return is_sequence(data) and all(map(is_sequence, list(data.raw_value)))


def is_number(data):
    """ is data a number
    """
    return isinstance(data, (int, long, float, bool, complex))


def is_str(v):
    return isinstance(v, str)


def qualified_type(value):
    """ Qualified type name, like 'numpy.int32'.
    Built-in types returned without qualifier.
    Note: module aliases are not supported!
    E.g.: "import numpy as np" will cause a further failure
    in a forced typecasting from editor to the python shell
    (or in a json import),
    because the name 'numpy' is not defined!
    """
    var_type = type(value)
    module_name = var_type.__module__
    type_name = var_type.__name__
    if module_name == '__builtin__':
        # return short name for standard types
        return type_name
    # return qualified name <module>.<type>
    return '{}.{}'.format(module_name, type_name)


def format_size(value):
    """ Size of list including any nested lists - formatted
    """

    def get_shape(a):
        shape = np.shape(np.array(a))
        if len(shape) < 2:
            shape = (1,) + shape
        return shape

    def str_recursive(a):
        if is_sequence(a):
            return map(str_recursive, a)
        return str(a)

    if is_sequence(value):
        return "x".join(map(str_recursive, get_shape(value)))
    if hasattr(value, '__len__'):
        return str(len(value))
    return '1'

# EOF
