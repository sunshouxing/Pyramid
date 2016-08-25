# -*- coding: utf-8 -*-

# ---- Import ------------------------------------------------------------
import json
from operator import itemgetter

import numpy as np
import scipy.io as sio
from pyface.api import FileDialog, OK, NO, confirm
from traits.api import \
    HasTraits, Instance, Any, Bool, Str, List, Tuple, Dict, Property, Button, \
    DelegatesTo, Event, TraitType, cached_property, on_trait_change
from traitsui.api import \
    View, UCustom, UReadonly, UItem, TextEditor, TableEditor, ShellEditor, \
    ObjectColumn, Label, HGroup, VGroup, VSplit, Controller, Menu, Action, Separator

from event_bus import EventBus


# ############################################
#
# Helpers
#
# ############################################


def has_items(v):
    """ Value has child items """
    return hasattr(v, '__iter__') and not isinstance(v, (str))


def is_sequence(v):
    """ Value is like array """
    return has_items(v) and not isinstance(v, (dict))


def is_mutable_sequence(v):
    """ Value like array which support mutation """
    return is_sequence(v) and hasattr(v, '__setitem__')


def is_number(v):
    """ Simple number-like value"""
    return isinstance(v, (int, long, float, bool, complex))


def is_str(v):
    return isinstance(v, str)


def q_type(value):
    """ 
    Qualified type name, like 'numpy.int32'.
    Built-in types returned without qualifier.
    Note: module aliases are not supported!
    E.g.: "import numpy as np" will cause a further failure
    in a forced typecasting from editor to the python shell
    (or in a json import), 
    because the name 'numpy' is not defined!
    """
    ptype = type(value)
    modname = ptype.__module__
    tname = ptype.__name__
    if modname == '__builtin__':
        # return short name for standard types
        return tname
    # return qualified name <module>.<typename>
    return '{}.{}'.format(modname, tname)


class DataExplorerError(Exception):
    """ Generic error in Variable Explorer """
    pass


def _format_size(value):
    """ Size of list including any nested lists - formatted """

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


def _compute_shape(value):
    return _format_size(value).split('x')


# ############################################
#
# Shortcuts
#
# ############################################

# ############################################
#
# Models
#
# ############################################


class RowModel(HasTraits):
    """
    ############################################
    Data model for row in variable explorer
    and for json export
    ############################################
    """

    fname = Str('')

    raw_value = Any('')

    ftype = Str('')
    fstatement = Str('')

    @on_trait_change('raw_value')
    def _handle_value_changed(self):
        self.ftype = q_type(self.raw_value)
        self.fsize = _format_size(self.raw_value)

    def __str__(self):
        return "<{}, {}:{}>".format(self.__class__.__name__, self.fname, self.raw_value)

    def __repr__(self):
        return "<{}, {}:{}>".format(self.__class__.__name__, self.fname, self.raw_value)


demo_data = {
    's':'aaa',
    'a':1,
    'b':2L,
    'pi':3.1416,
    'j':(1,2,3),
    'k':[1,2,3],
    # 'm':[
    #     [
    #         [1,2], [3,4],
    #     ],
    #     [
    #         [10,20], [30,40],
    #     ],
    #     [
    #         [100,200], [300,400, [500,600]],
    #     ]
    # ],
    # 'm':[1,2,'x'],
    'd2':dict(a=dict(aa=1,ab=2),b=dict(ba=3,bb=4)),
    'd':{'x':1,'a':"string","b":[[0,1],[2,3]]},
    'a2d':[[0,1],[2,3],[4,5]],
    'dd':{'a':[0,1],'b':[2,3],'c':[4,5,6]},
}

# relation between type and a factory function
types_registry = {
    'numpy.ndarray': 'numpy.array',
}


class VariableExplorerModel(HasTraits):
    """
    ############################################
    Data model for entire variable explorer
    ############################################
    """

    command_executed = Event

    def _command_executed_fired(self, v):
        print 'command_executed: ', v

    command_to_execute = Event

    def _command_to_execute_fired(self, v):
        print 'command_to_execute: ', v

    # Set of user-defined variables:
    # used both for view and for export
    var_list = List([RowModel()])

    # Pyhon environment:
    var_space = Dict

    # list of rows - for multi-selection
    # (filtered subset for export)
    selected_rows = List(RowModel)

    def __init__(self, **traits):
        HasTraits.__init__(self, **traits)
        if not self.var_space:
            self.var_space = demo_data

    def _var_space_changed(self):
        # clear the variables set and the selection:
        self.selected_rows[:] = []
        # update view:
        self.var_list[:] = [
            RowModel(fname=name, raw_value=value) \
            for name, value in self.var_space.items() \
            # if  (name != '__builtins__')]
            if (name != '__builtins__' and type(value).__name__ != 'module')]
        if len(self.var_list) == 0:
            self.var_list[:] = [RowModel()]

    def _var_space_items_changed(self, info):
        self._var_space_changed()

    def to_json_dict(self, selection_only=False):

        def parse_node(node):

            buff = {'type': q_type(node)}
            if isinstance(node, dict):
                buff['value'] = dict([(k, parse_node(v)) for k, v in node.items()])
            elif is_sequence(node):
                buff['value'] = [parse_node(v) for v in node]
            else:
                buff['value'] = node
            return buff

        buff = {}

        # select source for export:
        if selection_only:
            source = self.selected_rows
        else:
            source = self.var_list

        for order, row in enumerate(source):
            buff[row.fname] = parse_node(row.raw_value)
            buff[row.fname]['order'] = order
        return buff

    def from_json_dict(self, d):
        def parse_item_info(info):
            value = info['value']
            if isinstance(value, dict):
                buff = {}
                for k, v in value.items():
                    buff[k] = parse_item_info(v)
            elif is_sequence(value):
                buff = []
                for v in value:
                    buff.append(parse_item_info(v))
            else:
                buff = value
            _type = info['type']
            # load modules if any specified in a qualified type:
            tags = _type.split('.')
            if len(tags) > 1:
                # trim "type" itself
                tags = tags[:-1]
                modname = tags[-1]
                # in case if module in a package:
                q_modname = '.'.join(tags)
                self.var_space[modname] = eval('__import__({!r})'.format(q_modname), self.var_space)
                print 'imported module: {} {}; type: {}'.format(modname, q_modname, _type)
            return eval('{}({})'.format(_type, repr(buff)), self.var_space)

        _list = [dict(var_name=k, **v) for k, v in d.items()]
        _list.sort(key=itemgetter('order'))
        buff = {}
        self.var_space.clear()
        for row in _list:
            buff[row['var_name']] = parse_item_info(row)
            # value = eval('{}({})'.format(defs['ftype'], defs['raw_value']), self.var_space)
            # buff[name] = value
        self.var_space.update(buff)
        # print 'var_space: ', self.var_space
        # print 'var_list: ', self.var_list

    def from_mat_file(self, file_name):
        """ Allows to convers mat_structs into plain Python dicts"""

        def loadmat(filename):
            '''
            this function should be called instead of direct sio.loadmat
            as it cures the problem of not properly recovering python dictionaries
            from mat files. It calls the function check keys to cure all entries
            which are still mat-objects 
            '''
            data = sio.loadmat(filename, struct_as_record=False, squeeze_me=True)
            return _check_keys(data)

        def _check_keys(dict):
            '''
            checks if entries in dictionary are mat-objects. If yes
            todict is called to change them to nested dictionaries
            '''
            for key in dict.keys():
                if isinstance(dict[key], sio.matlab.mio5_params.mat_struct):
                    dict[key] = _todict(dict[key])
            return dict

        def _todict(matobj):
            '''
            A recursive function which constructs from matobjects nested dictionaries
            '''
            dict = {}
            for strg in matobj._fieldnames:
                elem = matobj.__dict__[strg]
                if isinstance(elem, sio.matlab.mio5_params.mat_struct):
                    dict[strg] = _todict(elem)
                elif isinstance(elem, np.ndarray):
                    dict[strg] = _tolist(elem)
                else:
                    dict[strg] = elem
            return dict

        def _tolist(ndarray):
            '''
            A recursive function which constructs lists from cellarrays 
            (which are loaded as numpy ndarrays), recursing into the elements
            if they contain matobjects.
            '''
            elem_list = []
            for sub_elem in ndarray:
                if isinstance(sub_elem, sio.matlab.mio5_params.mat_struct):
                    elem_list.append(_todict(sub_elem))
                elif isinstance(sub_elem, np.ndarray):
                    elem_list.append(_tolist(sub_elem))
                else:
                    elem_list.append(sub_elem)
            return elem_list

        buff = loadmat(file_name)
        self.var_space.clear()
        if 'numpy' not in buff:
            buff['numpy'] = eval('__import__("numpy")', buff)
        del buff['__header__']
        del buff['__version__']
        del buff['__globals__']
        self.var_space.update(buff)
        # print 'var_space: ', self.var_space
        # print 'var_list: ', self.var_list

    def to_mat_file(self, file_name, selection_only=False):
        # buff = self.to_json_dict()
        buff = {}

        # select source for export:
        if selection_only:
            source = self.selected_rows
        else:
            source = self.var_list

        for row in source:
            buff[row.fname] = row.raw_value
        sio.savemat(file_name, buff)

    def _selected_rows_changed(self):
        print 'Selection len: {}'.format(len(self.selected_rows))


# ############################################
#
# Views
#
# ############################################

variable_inspector = TableEditor(
    columns_name='controller.inspector.editor_columns',
    selection_mode='cell',
    selected='inspector_selected_cell',
    editable=True,
    deletable=False,
    sortable=False,
    rows=3,
    auto_size=True,
    # on_select='controller.handle_inspector_cell_select',
    edit_on_first_click=False,
    click='controller.inspector_cell_clicked',
    format_func=lambda v: '' if v is None else v,
)




# ############################################
#
# Controllers
#
# ############################################


# ############################################
# Inspector
# ############################################


# def _to_editor(value):
#     print "_to_editor: ", repr(value), type(value)
#     return repr(value)

# def _from_editor(value):
#     # return value
#     code = str(value)
#     print "eval: ", code, repr(code), type(code)
#     return eval(code)



def _inspector_col_factory( \
        name=None, \
        label='', \
        width=0.1, \
        readonly=False, \
        **kwargs):
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
            multi_line=False),

        **kwargs)


class DataInspectorRecord(HasTraits):
    """ 
    Editor proxy for plain types.
    Note that the "name" can contain either a name of variable or an index of a list item. 
    """
    var_root = Any(None)
    environment = Dict()
    name = Any('')
    readonly = Bool(False)

    # name or index of selected item 
    # for complex data structures
    # (used in descendants)

    raw_value = Property

    def _get_raw_value(self):
        if self.var_root is not None:
            try:
                return self.var_root[self.name]
            except KeyError, IndexError:
                pass
        else:
            return None

    def _set_raw_value(self, v):
        if self.readonly:
            return
        if self.var_root is not None and self.var_root[self.name] != v:
            self.var_root[self.name] = v
            if self.on_change:
                self.on_change()

    value = Property(depends_on='raw_value')

    # @cached_property
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
        _inspector_col_factory(name='value', label='', width=0.1)
    ])
    # interface foor exchange with editor:
    # editor_buffer = List([HasTraits(value='')])
    editor_buffer = Property

    @cached_property
    def _get_editor_buffer(self):
        return [self]

    def __init__(self, on_change=None, **traits):
        HasTraits.__init__(self, **traits)
        self._type = q_type(self.raw_value)
        self.on_change = on_change

    def __del__(self):
        self.environment = {}
        self.var_root = self.on_change = None

    # root, address, value
    def cell_info(self, col_name):
        """ Get raw data for the table cell (inspector) """
        item_label = ''
        return (self.var_root, self.name, self.raw_value, item_label)


class _SequenceItem(TraitType):
    """ Representaion of value from list in a TableEditor """

    def __init__(self, var_root={}, index=-1, environment={}, on_change=None, **metadata):
        self.var_root = var_root
        self.index = index
        self.environment = environment
        self.on_change = on_change
        self._type = None
        try:
            self._type = q_type(var_root[index])
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
            # print '_SequenceItem: IndexError in set'
            pass


class _SequenceRow(HasTraits):
    """ 
    Single row representation for a list inside inspector.
    Multi-dimensional list can occupy a several rows.
    """
    var_root = Any

    def __init__(self, **traits):
        HasTraits.__init__(self, **traits)
        self._mapping = {}
        self._items_labels = {}

    def append(self, \
               index=-1, \
               col_name='AA1', \
               environment={}, \
               on_change=None,
               item_label=''):

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
    def cell_info(self, col_name):
        """ Get raw data for the table cell (inspector) """
        root = self.var_root
        addr = self._mapping.get(col_name, -1)
        item_label = self._items_labels.get(col_name, '')
        try:
            value = root[addr]
        except IndexError:
            value = None
        return (root, addr, value, item_label)


class DataInspectorSequence(DataInspectorRecord):
    """ Editor proxy for sequences """

    def _is_matrix(self):
        return is_sequence(self.raw_value) and all(map(is_sequence, list(self.raw_value)))

    def _cols_count(self):
        if self._is_matrix():
            try:
                return max(*[len(list(item)) if is_sequence(item) else 0 for item in list(self.raw_value)]) + 1
            except TypeError:
                return 2
        return len(self.raw_value) + 1

    editor_columns = Property

    @cached_property
    def _get_editor_columns(self):
        cols = [
            _inspector_col_factory(
                name='AA{}'.format(i + 1),
                label=str(i + 1),
                width=0.1,
                readonly=self.readonly) for i in range(self._cols_count())]
        cols[-1].editable = False
        return cols

    editor_buffer = Property

    # @cached_property
    def _get_editor_buffer(self):
        buff = []
        if self._is_matrix():

            # scan by items as rows:
            for row_index in range(len(self.raw_value)):
                item = self.raw_value[row_index]
                row = _SequenceRow(var_root=item)
                buff.append(row)
                for col_index in range(self._cols_count()):
                    row.append(
                        index=col_index, \
                        col_name=self.editor_columns[col_index].name, \
                        environment=self.environment, \
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
        return (self.var_root, self.name, self.raw_value, '[{!r}]'.format(self.name))


class DataInspectorDict(DataInspectorRecord):
    """ Editor proxy for 'dict' type """

    editor_columns = List([
        _inspector_col_factory(label='Field', name='name', width=0.4, readonly=True),
        _inspector_col_factory(label='Value', name='value', width=0.2),
        _inspector_col_factory(label='Min', name='vmin', width=0.2, readonly=True),
        _inspector_col_factory(label='Max', name='vmax', width=0.2, readonly=True),
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


def inspector_factory(var_root, name, environment, on_change=None):
    """ Create an inspector instance depending on the value type"""
    try:
        value = var_root[name]
    except KeyError, IndexError:
        value = None

    if isinstance(value, dict):
        return DataInspectorDict(
            name=name, \
            var_root=var_root, \
            environment=environment, \
            on_change=on_change)
    elif is_sequence(value):
        return DataInspectorSequence(
            name=name, \
            var_root=var_root, \
            readonly=not is_mutable_sequence(value), \
            environment=environment, \
            on_change=on_change)
    else:
        return DataInspectorRecord(
            name=name, \
            var_root=var_root, \
            environment=environment, \
            on_change=on_change)


class DataExplorer(Controller):
    """Sub-application controller
    """

    # inter-app commands and notifications
    event_bus = Instance(EventBus)
    command = DelegatesTo('event_bus')
    args = DelegatesTo('event_bus')

    bt_command = Button(u' ')

    # root object to browse variables
    var_root = Any

    # the name of variable (the first selected row for multi-selection)
    selected_name = Any

    inspector = Instance(DataInspectorRecord)

    path_tags = List()
    inspector_label = Str('')
    path = Property(depends_on='path_tags,inspector_label')

    def _get_path(self):
        return '{}{}'.format(''.join(self.path_tags), self.inspector_label)

    inspector_cell_clicked = Event
    inspector_selected_cell = Tuple

    def __init__(self, *args, **traits):
        super(DataExplorer, self).__init__(*args, **traits)
        self.inspector = DataInspectorRecord()
        self.var_root = self.model.var_space
        # add notification handler to reflect val_space changes in the inspector
        self.model.on_trait_change(self._update_inspector, 'var_list[]')

    def init_inspector(self, root, name):
        # update active inspector
        self.inspector = inspector_factory(
            root, \
            name, \
            self.model.var_space, \
            self._update_editor)
        # clear info for the item selected in the inspector:
        self.inspector_label = ''

    def handle_row_select(self, rows):
        if rows:
            active_row = rows[0]  # single selection
            if active_row:
                self.selected_name = active_row.fname

                # sync the current level to the models' top:
                self.var_root = self.model.var_space

                name, root = self.selected_name, self.var_root
                if name in root:
                    self.path_tags = ['Browsing: <{}>{}'.format(type(root[name]).__name__, name)]
                else:
                    self.path_tags = []

                self.init_inspector(self.var_root, self.selected_name)

    def _inspector_selected_cell_changed(self, selection):

        inspector_row, col_name = self.inspector_selected_cell
        if inspector_row is not None:
            root, addr, value, item_label = inspector_row.cell_info(col_name)
            self.inspector_label = item_label

    def _inspector_cell_clicked_fired(self, cell_data):

        inspector_row, col_name = self.inspector_selected_cell

        if inspector_row is None:
            return

        root, addr, value, item_label = inspector_row.cell_info(col_name)

        # if value is None:
        #     return

        # if self.var_root != root and (isinstance(value, dict) or is_mutable_sequence(value)):
        if (isinstance(value, dict) or is_mutable_sequence(value)):
            self.var_root = root
            self.selected_name = addr
            self.init_inspector(root, addr)

            # update "path" to display "location" inside a variable items tree
            self.path_tags.append('[{!r}]'.format(addr))

    def _update_inspector(self):
        """
        Resresh inspector view after changes of model.var_space
        via the command line, while selection in var_list
        remains the same
        """
        self.init_inspector(self.var_root, self.selected_name)

    # ---------------------------------------
    # Event/command handlers:
    # ---------------------------------------
    def _command_changed(self):
        """ Command dispatcher """
        command = self.command
        # FIXME delete debug info
        print 'command: ', self.command
        # if <str> command is not "empty"
        if command:
            # find command handler in own methods
            try:
                handler = getattr(self, '_{}'.format(command))
                # FIXME delete debug info
                print 'handler: ', handler.__name__
            except AttributeError:
                # ignore command if handler not defined
                return

            handler(self.args)

    def _CMD_IMPORT(self, file_name):
        """ Handler for external command """
        # reset inspector:
        # self.inspector = DataInspectorRecord()

        ext = file_name.split('.')[-1]
        if ext == 'mat':
            # self.model.from_json_dict(buff)
            self.model.from_mat_file(file_name)

        elif ext == 'json':
            buff = ''
            with open(file_name, 'rb') as f:
                buff = f.read()
            model = json.loads(buff)
            self.model.from_json_dict(model)

        else:
            raise DataExplorerError('Unsupported file format: {}'.format(ext))

        # update initial selection - first row:
        if len(self.model.var_list) > 0:
            self.handle_row_select([self.model.var_list[0]])

    def _CMD_EXPORT_SELECTED(self, file_name):
        """ Handler for external command """
        self.__switch_command_export(file_name, selection_only=True)

    def _CMD_EXPORT(self, file_name):
        """ Handler for external command """
        self.__switch_command_export(file_name, selection_only=False)

    def __switch_command_export(self, file_name, selection_only):
        """ Helps to avoid repeated code """
        ext = file_name.split('.')[-1]
        if ext == 'mat':
            self.model.to_mat_file(file_name, selection_only)
        elif ext == 'json':
            print "exporting to: ", file_name
            buff = self.model.to_json_dict(selection_only)
            buff = json.dumps(buff)
            with open(file_name, 'wb') as f:
                f.write(buff)
        else:
            raise DataExplorerError('Unsupported file format: {}'.format(ext))

    def _update_editor(self):
        """ 
        Force updates in TableEditor 
        by add/remove of empty row to the end
        """
        root = self.model.var_list
        root.append(RowModel(fname='', raw_value=''))
        del root[-1]

    # ---------------------------------------
    # Menu actions:
    # ---------------------------------------

    def _menu_select_all(self, uiinfo, selection):
        """ Handle menu item """
        print selection, uiinfo
        self.model.selected_rows = self.model.var_list[:]
        print "selection: {}".format(len(self.model.selected_rows))

    def _menu_import(self, uiinfo, selection):
        """ Handle menu item """
        print '_menu_import'
        # f_name = open_file(filter=['*.mat', '*.json'], title='Title')
        # print f_name
        dlg = FileDialog(parent=uiinfo.ui.control, action='open',
                         wildcard="MATLAB files (*.mat)|*.mat|JSON files (*.json)|*.json")
        if dlg.open() == OK:
            print "Opening:", dlg.path
            self.event_bus.fire_event('CMD_IMPORT', dlg.path)

    def _menu_do_export_selected(self, uiinfo, selection):
        """ Handle menu item """
        print '_menu_do_export_selected'
        self.__switch_menu_export(uiinfo, 'CMD_EXPORT_SELECTED')

    def _menu_do_export(self, uiinfo, selection):
        """ Handle menu item """
        print '_menu_do_export'
        self.__switch_menu_export(uiinfo, 'CMD_EXPORT')

    def __switch_menu_export(self, uiinfo, send_command):
        """ Helps to avoid repeated code """

        dlg = FileDialog(parent=uiinfo.ui.control, action='save as',
                         wildcard="MATLAB files (*.mat)|*.mat|JSON files (*.json)|*.json")
        if dlg.open() == OK:
            import os
            if os.path.exists(dlg.path):
                msg = "File %r alreay exists. Do you want to overwrite?" % dlg.path
                if confirm(uiinfo.ui.control, msg) == NO:
                    return
            print "Saving:", dlg.path
            self.event_bus.fire_event(send_command, dlg.path)

    # ---- View definition -----------------------------------------------
    table_editor = TableEditor(
        columns=[
            ObjectColumn(
                name="fname",
                label=u"Name",
                horizontal_alignment="left",
                style="simple",
                width=0.2
            ),
            ObjectColumn(
                name="ftype",
                label=u"Type",
                horizontal_alignment="left",
                width=0.2
            ),
            ObjectColumn(
                name="fsize",
                label=u"Size",
                horizontal_alignment="left",
                format_func=lambda b: b if b else '',
                width=0.1
            ),
            ObjectColumn(
                name="raw_value",
                label=u"Value",
                horizontal_alignment="left",
                width=0.5,
                style='readonly',
                format_func=lambda b: str(b),
            ),
        ],
        editable=False,
        deletable=True,
        sortable=False,
        selection_mode='rows',
        orientation='vertical',

        auto_size=True,
        # row_factory=RowModel,
        # show_toolbar=True,
        rows=3,
        # handler for selection:
        on_select='controller.handle_row_select',
        selected='object.selected_rows',
        menu=Menu(
            Action(
                id='data_explorer_select_all',
                name=u'全选',
                action='_menu_select_all',
                enabled_when='len(object.var_list)>0'),
            Separator(),
            Action(
                id='data_explorer_import',
                name=u'导入...',
                action='_menu_import'),
            Separator(),
            Action(
                id='data_explorer_export_selected',
                name=u'导出选中...',
                action='_menu_do_export_selected',
                enabled_when='len(object.var_list)>0'),
            Action(
                id='data_explorer_export_all',
                name=u'导出全部...',
                action='_menu_do_export',
                enabled_when='len(object.var_list)>0'),
        )
    )

    traits_view = View(
        VGroup(
            VSplit(
                # explorer for all data
                HGroup(
                    Label(' '),
                    UCustom('object.var_list', editor=table_editor),
                    Label(' '),
                ),
                # single data inspector
                VGroup(
                    HGroup(
                        Label(' '),
                        UReadonly('controller.path'),
                        Label(' '),
                    ),
                    HGroup(
                        Label(' '),
                        UCustom('controller.inspector.editor_buffer', editor=variable_inspector),
                        Label(' '),
                    ),
                ),
                # command line tool
                HGroup(
                    Label(' '),
                    UItem(
                        "object.var_space",
                        editor=ShellEditor(
                            share=True,
                            command_executed='object.command_executed',
                            command_to_execute='object.command_to_execute',
                        ),
                        width=450,
                        tooltip=u'Enter the statement and press Enter',
                        has_focus=True,
                    ),
                    Label(' '),
                ),

            ),
            VGroup(
                Label(' '),
            )
        ),
        width=600,
        height=700,
        resizable=False,
        title=u'数据浏览器',
        # handler=HandleEvent
    )


model = VariableExplorerModel

if __name__ == '__main__':
    model = model()
    event_bus = EventBus()
    DataExplorer(model=model, event_bus=event_bus).configure_traits()
