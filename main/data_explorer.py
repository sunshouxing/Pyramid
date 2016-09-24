# -*- coding: utf-8 -*-

# ---- Import -------------------------------------------------------------
import json
from operator import itemgetter

import scipy.io as sio
from pyface.api import FileDialog, OK, NO, confirm
from traits.api import \
    HasTraits, Int, Str, List, Tuple, Dict, Any, Instance, \
    Property, DelegatesTo, Event, on_trait_change, cached_property
from traitsui.api import \
    View, UCustom, UReadonly, UItem, TableEditor, ShellEditor, \
    ObjectColumn, Label, HGroup, VGroup, VSplit, Controller, Menu, Action, Separator

from data_common import *
from data_inspector import \
    DataInspectorRecord, DataInspectorSequence, DataInspectorDict
from event_bus import EventBus

import workspace

demo_data = {
    's': 'aaa',
    'a': 1,
    'b': 2L,
    'pi': 3.1416,
    'j': (1, 2, 3),
    'k': [1, 2, 3],
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
    'd2': dict(a=dict(aa=1, ab=2), b=dict(ba=3, bb=4)),
    'd': {'x': 1, 'a': "string", "b": [[0, 1], [2, 3]]},
    'a2d': [[0, 1], [2, 3], [4, 5]],
    'dd': {'a': [0, 1], 'b': [2, 3], 'c': [4, 5, 6]},
}


def _compute_shape(value):
    return format_size(value).split('x')


def inspector_factory(var_root, name, environment, on_change=None):
    """ Create an inspector instance depending on the value type
    """
    try:
        value = var_root[name]
    except KeyError:
        value = None

    if isinstance(value, dict):
        return DataInspectorDict(
            name=name,
            var_root=var_root,
            environment=environment,
            on_change=on_change
        )
    elif is_sequence(value):
        return DataInspectorSequence(
            name=name,
            var_root=var_root,
            readonly=not is_mutable_sequence(value),
            environment=environment,
            on_change=on_change
        )
    else:
        return DataInspectorRecord(
            name=name,
            var_root=var_root,
            environment=environment,
            on_change=on_change
        )


class DataExplorerError(Exception):
    """ generic error used by Data Explorer
    """
    pass


class RowModel(HasTraits):
    """ data model for row in variable explorer and for json export
    """

    field_name = Str('')

    raw_value = Any('')

    field_type = Str('')

    field_size = Str

    field_statement = Str('')

    def __init__(self, name, value):
        self.field_name = name
        self.raw_value = value
        self.field_type = qualified_type(value)
        self.field_size = format_size(value)

    @on_trait_change('raw_value')
    def _handle_value_changed(self):
        self.field_type = qualified_type(self.raw_value)
        self.field_size = format_size(self.raw_value)

    def __str__(self):
        return "<{}, {}:{}>".format(self.__class__.__name__, self.field_name, self.raw_value)

    def __repr__(self):
        return "<{}, {}:{}>".format(self.__class__.__name__, self.field_name, self.raw_value)


class DataModel(HasTraits):
    """ Data model for entire data explorer
    """
    # command_to_execute = Event

    # list of RowModels represents data in data_space, used for both view and export
    data_list = List(RowModel)
    # python environment
    workspace = Instance()
    data_space = DelegatesTo('workspace', prefix='data')

    # list of RowModels - for multi-selection (filtered subset for export)
    selected_rows = List(RowModel)

    def __init__(self, workspace, **traits):
        super(DataModel, self).__init__(**traits)
        self.workspace = workspace

    # --------------------------------------
    # DataModel trait listener
    # --------------------------------------
    # def _command_to_execute_fired(self, v):
    #     print 'command_to_execute: ', v

    def _selected_rows_changed(self):
        # FIXME debug info
        print('DEBUG: {} rows selected.'.format(len(self.selected_rows)))

    def _data_space_changed(self):
        # FIXME debug info
        print('DEBUG: var space changed')

        # clear the variables set and the selection:
        self.selected_rows[:] = []
        # update view
        self.data_list[:] = [
            RowModel(name, value) for name, value in self.data_space.items()
            if (name != '__builtins__' and type(value).__name__ != 'module')
        ]

        if len(self.data_list) == 0:
            self.data_list[:] = [RowModel()]

    def _data_space_items_changed(self):
        self._data_space_changed()

    # ---------- end of listeners -----------

    def to_json_dict(self, selection_only=False):

        def parse_node(node):
            buff = {'type': qualified_type(node)}
            if isinstance(node, dict):
                buff['value'] = dict([(k, parse_node(v)) for k, v in node.items()])
            elif is_sequence(node):
                buff['value'] = [parse_node(v) for v in node]
            else:
                buff['value'] = node

            return buff

        buff = {}

        # select source for export
        source = (selection_only and self.selected_rows or self.data_list)

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
                self.data_space[modname] = eval('__import__({!r})'.format(q_modname), self.data_space)
                print 'imported module: {} {}; type: {}'.format(modname, q_modname, _type)
            return eval('{}({})'.format(_type, repr(buff)), self.data_space)

        _list = [dict(var_name=k, **v) for k, v in d.items()]
        _list.sort(key=itemgetter('order'))
        buff = {}
        self.data_space.clear()
        for row in _list:
            buff[row['var_name']] = parse_item_info(row)
        self.data_space.update(buff)

    def from_mat_file(self, file_name):
        """ Allows to load data from files saved by MATLAB into plain Python dicts
        """

        def loadmat(filename):
            """
            this function should be called instead of direct sio.loadmat
            as it cures the problem of not properly recovering python dictionaries
            from mat files. It calls the function check keys to cure all entries
            which are still mat-objects
            """
            data = sio.loadmat(filename, struct_as_record=False, squeeze_me=True)
            return _check_keys(data)

        def _check_keys(dict):
            """
            checks if entries in dictionary are mat-objects. If yes
            todict is called to change them to nested dictionaries
            """
            for key in dict.keys():
                if isinstance(dict[key], sio.matlab.mio5_params.mat_struct):
                    dict[key] = _todict(dict[key])
            return dict

        def _todict(matobj):
            """
            A recursive function which constructs from matobjects nested dictionaries
            """
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
            """
            A recursive function which constructs lists from cell arrays
            (which are loaded as numpy ndarrays), recursing into the elements
            if they contain matobjects.
            """
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
        self.data_space.clear()
        if 'numpy' not in buff:
            buff['numpy'] = eval('__import__("numpy")', buff)
        del buff['__header__']
        del buff['__version__']
        del buff['__globals__']
        self.data_space.update(buff)

    def to_mat_file(self, file_name, selection_only=False):
        # buff = self.to_json_dict()
        buff = {}

        # select source for export:
        if selection_only:
            source = self.selected_rows
        else:
            source = self.data_list

        for row in source:
            buff[row.fname] = row.raw_value
        sio.savemat(file_name, buff)


class DataInspector(Controller):
    # ---- Traits definition ----------------------------------------------

    # event used to response data_inspector's cell clicked
    cell_clicked = Event
    # selected cell details, used as data_inspector's selected parameter
    selected_cell = Tuple

    inspector_label = Str('')
    path_tags = List
    data_label = Property(depends_on='path_tags,inspector_label')

    # ---- View definition ------------------------------------------------
    inspector_editor = TableEditor(
        columns_name='editor_columns',
        selection_mode='cell',
        selected='selected_cell',
        rows=3,
        sortable=False,
        auto_size=True,
        edit_on_first_click=False,
        click='handler.cell_clicked',
        format_func=lambda v: '' if v is None else v,
    )

    taints_view = View(
        VGroup(
            HGroup(
                '10',
                UReadonly('handler.data_label'),
                '10',
            ),
            HGroup(
                '10',
                UCustom('editor_buffer', editor=inspector_editor),
                '10',
            ),
        ),
    )

    def __init__(self, *args, **traits):
        super(DataInspector, self).__init__(*args, **traits)

    # ---- Traits listeners ----------------------------------------------
    def _cell_clicked_fired(self):
        inspector_row, column = self.selected_cell

        if inspector_row is not None:
            root, address, value, label = inspector_row.cell_info(column)
            if isinstance(value, dict) or is_mutable_sequence(value):
                self.var_root = root
                self.selected_name = address
                self.init_inspector(root, address)
                # update "path" to display "location" inside a variable items tree
                self.path_tags.append('[{!r}]'.format(address))

    def _selected_cell_changed(self):
        # FIXME debug info
        print('DEBUG: selected cell details: {}'.format(self.selected_cell))

        inspector_row, column_name = self.selected_cell
        if inspector_row is not None:
            root, address, value, label = inspector_row.cell_info(column_name)
            self.inspector_label = label

    # FIXME debug info
    def _inspector_label_changed(self, old, new):
        print('DEBUG: inspector label changed from {} to {}.'.format(old, new))

    # FIXME debug info
    def _path_tags_items_changed(self):
        print('DEBUG: path tags: {!s}'.format(self.path_tags))

    @cached_property
    def _get_data_label(self):
        return u'{}{}'.format(''.join(self.path_tags), self.inspector_label)

# end of DataInspector definition


class DataExplorer(Controller):
    """ sub-application controller
    """
    # inter-app commands and notifications
    event_bus = Instance(EventBus)
    # delegation of event bus' command
    command = DelegatesTo('event_bus')
    # delegation of event bus' command arguments
    args = DelegatesTo('event_bus')

    # root object to browse variables
    var_root = Any
    # the name of variable (the first selected row for multi-selection)
    selected_name = Any
    # inspector to show data details
    inspector = Instance(DataInspectorRecord)

    inspector_label = Str('')
    path_tags = List
    data_label = Property(depends_on='path_tags,inspector_label')

    # event used to response data_inspector's cell clicked
    inspector_cell_clicked = Event
    # selected cell details, used as data_inspector's selected parameter
    inspector_selected_cell = Tuple

    def __init__(self, *args, **traits):
        super(DataExplorer, self).__init__(*args, **traits)
        self.inspector = DataInspectorRecord()
        self.var_root = self.model.data_space
        # add notification handler to reflect val_space changes in the inspector
        self.model.on_trait_change(self._update_inspector, 'data_list[]')

    # --------------------------------------
    # trait listeners
    # --------------------------------------
    def _command_changed(self):
        """ Command dispatcher """
        command = self.command
        # FIXME debug info
        print('DEBUG: command changed to "{}"'.format(command))
        # if command is not "empty"
        if command:
            # find command handler in own methods
            try:
                handler = getattr(self, '_{}'.format(command))
                # FIXME debug info
                print('DEBUG: response command "{}" with handler {}'.format(command, handler.__name__))
            except AttributeError:
                # ignore command if handler not defined
                return

            handler(self.args)

    @cached_property
    def _get_data_label(self):
        return u'{}{}'.format(''.join(self.path_tags), self.inspector_label)

    def _inspector_cell_clicked_fired(self):
        inspector_row, column = self.inspector_selected_cell

        if inspector_row is None:
            return

        root, address, value, label = inspector_row.cell_info(column)
        if isinstance(value, dict) or is_mutable_sequence(value):
            self.var_root = root
            self.selected_name = address
            self.init_inspector(root, address)

            # update "path" to display "location" inside a variable items tree
            self.path_tags.append('[{!r}]'.format(address))

    def _inspector_selected_cell_changed(self):
        # FIXME debug info
        print('DEBUG: selected cell details: {}'.format(self.inspector_selected_cell))

        inspector_row, column_name = self.inspector_selected_cell
        if inspector_row is not None:
            root, address, value, label = inspector_row.cell_info(column_name)
            self.inspector_label = label

    # --------- end of listeners -----------

    def init_inspector(self, root, name):
        # update active inspector
        self.inspector = inspector_factory(root, name, self.model.data_space, self._update_editor)
        # clear info for the item selected in the inspector:
        self.inspector_label = ''

    def handle_row_select(self, rows):
        if rows:
            active_row = rows[0]  # single selection
            if active_row:
                self.selected_name = active_row.field_name

                # sync the current level to the models' top:
                self.var_root = self.model.data_space

                name, root = self.selected_name, self.var_root
                if name in root:
                    self.path_tags = [u'正浏览: <{}>{}'.format(type(root[name]).__name__, name)]
                else:
                    self.path_tags = []

                self.init_inspector(self.var_root, self.selected_name)

    def _update_inspector(self):
        """ refresh inspector view after changes in model.data_space
        via the command line, while selection in data_list
        remains the same
        """
        self.init_inspector(self.var_root, self.selected_name)

    # ---------------------------------------
    # Event/command handlers
    # ---------------------------------------

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
        if len(self.model.data_list) > 0:
            self.handle_row_select([self.model.data_list[0]])

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
        """ Force updates in TableEditor
        by add/remove of empty row to the end
        """
        root = self.model.data_list
        root.append(RowModel(name='', value=''))
        del root[-1]

    # ---------------------------------------
    # Menu actions
    # ---------------------------------------
    def _menu_select_all(self, uiinfo, selection):
        """ select all exist rows
        """
        print selection, uiinfo
        self.model.selected_rows = self.model.data_list[:]
        print "selection: {}".format(len(self.model.selected_rows))

    def _menu_import(self, ui_info):
        """ Handle menu item """
        dialog = FileDialog(
            parent=ui_info.ui.control,
            action='open',
            wildcard="MATLAB files (*.mat)|*.mat|JSON files (*.json)|*.json"
        )
        if dialog.open() == OK:
            # FIXME debug info
            print("DEBUG: importing data from {}...".format(dialog.path))
            self.event_bus.fire_event('CMD_IMPORT', dialog.path)

    def _menu_do_export_selected(self, uiinfo, selection):
        """ Handle menu item """
        self.__switch_menu_export(uiinfo, 'CMD_EXPORT_SELECTED')

    def _menu_do_export(self, uiinfo, selection):
        """ Handle menu item """
        self.__switch_menu_export(uiinfo, 'CMD_EXPORT')

    def __switch_menu_export(self, info, send_command):
        """ Helps to avoid repeated code """

        dialog = FileDialog(
            parent=info.ui.control,
            action='save as',
            wildcard="MATLAB files (*.mat)|*.mat|JSON files (*.json)|*.json"
        )
        if dialog.open() == OK:
            import os
            if os.path.exists(dialog.path):
                message = "File {} already exists. Do you want to overwrite?".formate(dialog.path)
                if confirm(info.ui.control, message) == NO:
                    return
            # FIXME debug info
            print('DEBUG: saving data to file {} ...'.format(dialog.path))
            self.event_bus.fire_event(send_command, dialog.path)

    # ---- View definition -----------------------------------------------
    table_editor = TableEditor(
        columns=[
            ObjectColumn(
                name="field_name",
                label=u"Name",
                horizontal_alignment="left",
                style="simple",
                width=0.2
            ),
            ObjectColumn(
                name="field_type",
                label=u"Type",
                horizontal_alignment="left",
                width=0.2
            ),
            ObjectColumn(
                name="field_size",
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
        rows=3,
        on_select='handler.handle_row_select',
        selected='object.selected_rows',
        menu=Menu(
            Action(
                id='data_explorer_select_all',
                name=u'全选',
                action='_menu_select_all',
                enabled_when='len(object.data_list)>0'),
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
                enabled_when='len(object.data_list)>0'),
            Action(
                id='data_explorer_export_all',
                name=u'导出全部...',
                action='_menu_do_export',
                enabled_when='len(object.data_list)>0'),
        )
    )

    data_inspector = TableEditor(
        columns_name='handler.inspector.editor_columns',
        selection_mode='cell',
        selected='handler.inspector_selected_cell',
        rows=3,
        sortable=False,
        edit_on_first_click=False,
        click='handler.inspector_cell_clicked',
        format_func=lambda v: '' if v is None else v,
    )

    traits_view = View(
        VGroup(
            VSplit(
                # explorer for all data
                HGroup(
                    '10',
                    UCustom('data_list', editor=table_editor),
                    '10',
                ),
                # single data inspector
                VGroup(
                    HGroup(
                        '10',
                        UReadonly('handler.data_label'),
                        '10',
                    ),
                    HGroup(
                        '10',
                        UCustom('handler.inspector.editor_buffer', editor=data_inspector),
                        '10',
                    ),
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


model = DataModel

if __name__ == '__main__':
    model = model(workspace=workspace)
    event_bus = EventBus()
    DataExplorer(model=model, event_bus=event_bus).configure_traits()
