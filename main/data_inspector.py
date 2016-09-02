# -*- coding: utf-8 -*-

# ---- Imports -----------------------------------------------------------
from traits.api import \
    HasTraits, Any, Bool, List, Dict, Property, TraitType, cached_property
from traitsui.api import \
    TextEditor, ObjectColumn

from data_common import *

# relation between type and a factory function
types_registry = {
    'numpy.ndarray': 'numpy.array',
}


def _inspector_column_factory(name=None, label='', width=0.1, readonly=False, **kwargs):
    return ObjectColumn(
        name=name,
        label=label,
        width=width,
        style=readonly and 'readonly' or 'custom',
        horizontal_alignment="left",
        format_func=lambda v: '' if v is None else v,
        editor=TextEditor(
            enter_set=True,
            auto_set=False,
            multi_line=False
        ),
        **kwargs
    )


class DataInspectorRecord(HasTraits):
    """ Editor proxy for plain types.
    Note that the "name" can contain either a name of variable or an index of a list item.
    """
    var_root = Any(None)
    environment = Dict()
    name = Any('')
    readonly = Bool(False)

    def __init__(self, on_change=None, **traits):
        super(DataInspectorRecord, self).__init__(**traits)
        self._type = qualified_type(self.raw_value)
        self.on_change = on_change

    def __del__(self):
        self.environment = {}
        self.var_root = None
        self.on_change = None

    # name or index of selected item for complex data structures (used in descendants)
    raw_value = Property

    def _get_raw_value(self):
        if self.var_root is None:
            return None

        try:
            return self.var_root[self.name]
        except KeyError:
            pass

    def _set_raw_value(self, v):
        if self.readonly:
            return
        if self.var_root is not None and self.var_root[self.name] != v:
            self.var_root[self.name] = v
            if self.on_change:
                self.on_change()

    value = Property(depends_on='raw_value')

    def _get_value(self):
        return repr(self.raw_value)

    def _set_value(self, v):
        # force typed value (e.g., for np.array, etc.):
        # subst type for "numpy factories"
        _type = types_registry.get(self._type, self._type)
        v = eval('{}({})'.format(_type, v), self.environment)
        if self.raw_value != v:
            self.raw_value = v

    # return columns for table
    editor_columns = List([
        _inspector_column_factory(name='value', label='', width=0.1)
    ])
    # interface for exchange with editor:
    # editor_buffer = List([HasTraits(value='')])
    editor_buffer = Property

    @cached_property
    def _get_editor_buffer(self):
        return [self]

    # root, address, value
    def cell_info(self, col_name):
        """ get raw data for the table cell (inspector)
        """
        item_label = ''
        return self.var_root, self.name, self.raw_value, item_label


class _SequenceItem(TraitType):
    """ representation of value from list in a TableEditor
    """

    def __init__(self, var_root={}, index=-1, environment={}, on_change=None, **metadata):
        self.var_root = var_root
        self.index = index
        self.environment = environment
        self.on_change = on_change
        self._type = None
        try:
            self._type = qualified_type(var_root[index])
        except IndexError:
            pass
        super(_SequenceItem, self).__init__(**metadata)

    def __del__(self):
        self.var_root = self.environment = self.on_change = None

    def get(self, object, name):
        root, index = self.var_root, self.index
        try:
            return repr(root[index])
        except IndexError:
            # print '_SequenceItem: IndexError in get'
            return None

    def set(self, object, name, v):
        root, index = self.var_root, self.index
        v = eval('{}({})'.format(self._type, v), self.environment)
        try:
            if root[index] != v:
                root[index] = v
                if self.on_change:
                    self.on_change()
        except IndexError:
            pass


class _SequenceRow(HasTraits):
    """
    single row representation for a list inside inspector,
    multi-dimensional list will occupy several rows.
    """
    var_root = Any

    def __init__(self, **traits):
        super(_SequenceRow, self).__init__(**traits)
        self._mapping = {}
        self._items_labels = {}

    def append(self, index=-1, col_name='AA1', environment={}, on_change=None, item_label=''):
        self.add_trait(
            col_name, \
            _SequenceItem(
                var_root=self.var_root, \
                index=index, \
                environment=environment, \
                on_change=on_change))

        self._mapping[col_name] = index
        self._items_labels[col_name] = item_label

    # root, address, value
    def cell_info(self, column):
        """ Get raw data for the table cell (inspector) """
        root = self.var_root
        address = self._mapping.get(column, -1)
        label = self._items_labels.get(column, '')
        try:
            value = root[address]
        except IndexError:
            value = None
        return root, address, value, label


class DataInspectorSequence(DataInspectorRecord):
    """ editor proxy for sequences
    """

    def _cols_count(self):
        if is_matrix(self):
            try:
                return max(*[len(list(item)) if is_sequence(item) else 0 for item in list(self.raw_value)]) + 1
            except TypeError:
                return 2
        # return len(self.raw_value) + 1
        return len(self.raw_value)

    editor_columns = Property

    @cached_property
    def _get_editor_columns(self):
        columns = [
            _inspector_column_factory(
                name='AA{}'.format(i + 1),
                label=str(i + 1),
                width=0.1,
                readonly=self.readonly) for i in range(self._cols_count())]
        columns[-1].editable = False
        return columns

    editor_buffer = Property

    # @cached_property
    def _get_editor_buffer(self):
        buff = []
        if is_matrix(self):
            # scan by items as rows:
            for row_index in range(len(self.raw_value)):
                item = self.raw_value[row_index]
                row = _SequenceRow(var_root=item)
                buff.append(row)
                for col_index in range(self._cols_count()):
                    row.append(
                        index=col_index,
                        col_name=self.editor_columns[col_index].name,
                        environment=self.environment,
                        on_change=self.on_change,
                        item_label='[{}][{}]'.format(row_index, col_index)
                    )
        else:
            row = _SequenceRow(var_root=self.raw_value)
            buff.append(row)
            for col_index in range(self._cols_count()):
                row.append(
                    index=col_index, \
                    col_name=self.editor_columns[col_index].name, \
                    environment=self.environment, \
                    on_change=self.on_change,
                    item_label='[{}]'.format(col_index)
                )
        return buff


class _DictPair(DataInspectorRecord):
    """Container for pair of key, value"""
    key = Property

    def _get_key(self):
        return self.name

    def _set_key(self, k):
        self.name = k

    vmin = Property(depends_on='raw_value')

    def _get_vmin(self):
        if is_sequence(self.raw_value):
            return min(*self.raw_value)
        else:
            return None

    vmax = Property(depends_on='raw_value')

    def _get_vmax(self):
        if is_sequence(self.raw_value):
            return max(*self.raw_value)
        else:
            return None

    # root, address, value
    def cell_info(self, col_name):
        """ Get raw data for the table cell (inspector) """
        return self.var_root, self.name, self.raw_value, '[{!r}]'.format(self.name)


class DataInspectorDict(DataInspectorRecord):
    """ Editor proxy for 'dict' type """

    editor_columns = List([
        _inspector_column_factory(label='Field', name='name', width=0.4, readonly=True),
        _inspector_column_factory(label='Value', name='value', width=0.2),
        _inspector_column_factory(label='Min', name='vmin', width=0.2, readonly=True),
        _inspector_column_factory(label='Max', name='vmax', width=0.2, readonly=True),
    ])

    editor_buffer = Property

    @cached_property
    def _get_editor_buffer(self):
        return [
            _DictPair(
                var_root=self.raw_value, \
                name=key, \
                environment=self.environment, \
                on_change=self.on_change
            ) for key in self.raw_value.keys()]

# EOF
