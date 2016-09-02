# -*- coding: utf-8 -*-
# fixture for Ubuntu - independent Python with Canopy packages bundle
try:
    import path_fix
except ImportError:
    pass

from event_bus import EventBus 

# from traits.api import \
#     HasTraits,\
#     Instance,\
#     Any,\
#     Str,\
#     List,\
#     Property,\
#     File,\
#     Directory,\
#     Enum,\
#     Button,\
#     on_trait_change,\
#     DelegatesTo

# from traitsui.api import \
#     View,\
#     Item,\
#     FileEditor,\
#     Label,\
#     HGroup,\
#     VGroup,\
#     Controller,\
#     Handler,\
#     UIInfo,\
#     spring,\
#     Menu,\
#     Action



from traits.api import \
    HasTraits, \
    Bool, \
    Str, \
    List, \
    Enum, \
    Tuple, \
    Instance, \
    Any, \
    Property, \
    Event, \
    cached_property, \
    on_trait_change, \
    DelegatesTo

from traitsui.api import \
    TextEditor, \
    TreeNodeObject, \
    EnumEditor, \
    ObjectTreeNode, \
    View, \
    Item, \
    Label, \
    VSplit, \
    HGroup, \
    VGroup, \
    Group, \
    Controller, \
    TreeEditor


from traitsui.menu import \
    Menu, \
    Action, \
    Separator

from os import \
    listdir as _listdir, \
    stat as _stat

import time

from os.path import \
    join as _join, \
    isdir as _isdir, \
    isfile as _isfile, \
    split as _split, \
    splitext as _splitext, \
    abspath as _abspath, \
    dirname as _dirname, \
    exists as _exists, \
    sep as _sep

import platform as _platform


# from traitsui.file_dialog \
#     import save_file, open_file

# ############################################
#
# Helpers
#
# ############################################

def _script_folder():
    import sys
    return _abspath(_dirname(sys.argv[0]))

_os_name = _platform.system().lower()

if _os_name.startswith('windows') :

    def _enum_root():
        import string
        from ctypes import windll

        drives = []
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.uppercase:
            if bitmask & 1:
                drives.append('{}:{}'.format(letter, _sep))
            bitmask >>= 1
        return drives

elif _os_name.startswith('linux'): 

    def _enum_root():
        return ['/']

else:
    import sys
    def _enum_root():
        path = _script_folder()
        while _split(path)[1]:
            path = _split(path)[0]
        return path


def scanfolder(path):
    try:
        return _listdir(path)
    except:
        return []


class FileExplorerError(Exception):
    """ Generic error in File Explorer """
    pass

# patched version of TreeEditor

from traitsui.qt4.tree_editor import SimpleEditor

class PatchedEditor(SimpleEditor):

    def init( self, parent ):
        SimpleEditor.init( self, parent )
        tree_model = self.value
        print "tree_model", tree_model
        tree_model.editor = self

    def _create_item(self, nid, node, object, index=None):
        """ Create  a new TreeWidgetItem as per word_wrap policy.

        Index is the index of the new node in the parent:
            None implies append the child to the end. """
        cnid = SimpleEditor._create_item(self, nid, node, object, index)

        # set reference to the toolkit widget:
        # object.deferred = False
        object.nid = cnid

        return cnid


class TreeEditorEx(TreeEditor):

    def _get_simple_editor_class(self):
        return PatchedEditor

    def _get_custom_editor_class(self):
        return PatchedEditor


class FileSystemEntity(TreeNodeObject):
    """ Abstract node in a filesystem """

    parent = Any

    sys_name = Any(None)

    path = Property

    info = Property

    deferred = Bool(False)

    display_tooltip = Property

    force_expand = Bool(False)

    nid = Any

    def _get_display_tooltip(self):
        """ display_tooltip = Property """
        info = self.info
        return \
            "{!s}: {!s} \nModified: {!s}\nSize:{!s} bytes"\
            .format(self.name, self.sys_name, info['last_modified'], info['size'])

    def _get_path ( self ):
        """ path = Property """
        return _join( self.parent.path, self.sys_name )

    @cached_property
    def _get_info ( self ):
        """ info = Property """
        try:
            (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = _stat(self.path)
            return dict(
                size = str(size),
                last_modified = time.ctime(mtime)
                )
        except Exception as e:
            print 'Exception', e
            return dict(
                size = '-',
                last_modified = '-'
                )

    def __repr__(self):
        return '<{}; name: {}, path: {}>'.format(self.__class__.__name__, self.sys_name, self.path)


    def refresh( self ):
        pass

    def init_items( self ):
        pass

    # ----------------------------------------
    # Intrface / protocol for TreeNodeObject:
    # ----------------------------------------
    def tno_get_label ( self, node ):
        return self.sys_name

    def tno_get_tooltip ( self, node ):
        return self.display_tooltip

    def tno_set_label ( self, node, label ):
        """ Sets the label for a specified object.
        """
        self.sys_name = label

    def tno_get_name ( self, node ):
        """ Returns the name to use when adding a new object instance
            (displayed in the "New" submenu).
        """
        return self.name

    def tno_get_menu ( self, node ):
        return node.menu

    def tno_can_auto_open ( self, node ):
        """ Returns whether the object's children should be automatically
        opened.
        """
        return self.force_expand

    def tno_can_auto_close ( self, node ):
        """ Returns whether the object's children should be automatically
        closed.
        to-do: planned for "expand" method (future)
        """
        return True


class FileEntity(FileSystemEntity):
    """ File node in a tree """

    # children = Str('')
    extension = Property

    name = Str('File')

    def _get_extension(self):
        _, ext = _splitext(self.sys_name)
        return ext



class FolderEntity(FileSystemEntity):
    """ Folder node in a tree """

    sys_name = Any(None)
    path = Property

    # children = Str('items')

    items = List([FileEntity()])

    filter = Tuple(('.json', '.mat'))

    name = Str('Folder')

    # store visibility status of children
    visited = Bool(False)

    # defer scanning of invisible folders
    deferred = Bool(True)

    needs_update = Event

    # path fragment which related to the path of the selected item in a FileSystemTree
    active_child_name = Str

    active_child = Property

    def __init__(self, sys_name=None, deferred=True, **traits):
        FileSystemEntity.__init__(self, **traits)
        self._dir_map = {}
        self._file_map = {}
        self.sys_name = sys_name
        self.deferred = deferred

    def tno_get_icon ( self, node, is_expanded ):
        """ Returns the icon for a specified object.
        """
        # Intercept status of this node:
        if not self.visited and is_expanded:
            self.visited = is_expanded

        return FileSystemEntity.tno_get_icon( self, node, is_expanded )

    def _get_path ( self ):
        if self.sys_name:
            if self.parent is not None:
                return _join( self.parent.path, self.sys_name )
            return self.sys_name
        return None

    def _active_child_name_changed( self, value ):
        if self.deferred:
            self.deferred = False
        found = None
        name = self.active_child_name
        for item in self.items:
            if item.sys_name == name:
                found = item
            else:
                item.force_expand = False
        if found:
            found.force_expand = True
        else:
            print "Item {} is not child of {}".format(name, self.sys_name)
        self._active_child = found

    def _get_active_child(self):
        return self._active_child

    def _force_expand_changed( self, value ):
        if self.nid:
            self.nid.setExpanded(self.force_expand)

    def _visited_changed( self, was_expanded, becomes_expanded ):
        if becomes_expanded and not was_expanded:
            # release all chidren to scan items:
            for child in self.items:
                if child.deferred:
                    child.deferred = False

    def _deferred_changed( self, was_deferred, deferred):
        if was_deferred and not deferred:
            self.refresh()
    
    def refresh( self ):
        self.items = []
        self.items = self._enum_items( )

    def rebuild( self ):
        self._dir_map = {}
        self._file_map = {}
        self.refresh()

    def _enum_items ( self ):
        """ Gets the object's children.
        """

        dirs  = []
        files = []
        path  = self.path
        for name in scanfolder( path ):
            if name.startswith('.'):
                continue
            cur_path = _join( path, name )
            if _isdir( cur_path ):
                item = self._dir_map.get(name, None)
                if not item:
                    item = FolderEntity( parent = self, sys_name = name )
                    self._dir_map[name] = item
                dirs.append( item )
            elif _isfile( cur_path ):
                _, ext = _splitext( name )
                if (ext in self.filter):
                    item = self._file_map.get(name, None)
                    if not item:
                        item = FileEntity( parent = self, sys_name = name )
                        self._file_map[name] = item
                    files.append( item )

        dirs.sort(  lambda l, r: cmp( l.sys_name.lower(), r.sys_name.lower() ) )
        files.sort( lambda l, r: cmp( l.sys_name.lower(), r.sys_name.lower() ) )

        return (dirs + files)



class FileSystemTree(FolderEntity):
    """ 
    Mount point with children (as a collection), 
    where children are mount points:
    Drive letter on Windows,
    '/' on *NIX
    """

    editor = Instance(PatchedEditor)

    # This is a topmost object in hierarchy
    parent = None

    path = Property

    visited = Bool(True)

    # defer scanning of invisible folders
    deferred = Bool(False)    

    selected = Instance(FileSystemEntity)

    def __init__(self, **traits):
        FolderEntity.__init__(self, **traits)
        self.refresh()

    def _get_path ( self ):
        return None

    def _set_path ( self, path ):
        """ 
        Try to select TreeNode which relates to the path.
        Note: This method does not allow to expand tree to the selected node.
        Reason: Underlying QtTreeWidgetItem with its' .setExpanded(True) is
        hidden inside TreeEditor for qt4 toolkit.
        to-do: try to auto-expand related nodes in a treeview control
        """
        print '==================='
        def walker( node, path_tags ):
            """ Recursive function to search node """

            # path_tags = path_tags[:]
            name = path_tags.pop()

            if 'items' in node.traits():

                node.active_child_name = name
                item = node.active_child

                if item:
                    item.deferred = False
                    # item.init_items()
                    item.force_expand = True

                    if path_tags:
                        return walker( item, path_tags )
                    else:
                        return item

                print 'Item "{}" not found in {}'.format(name, node.items)
                return None
            else:
                print "Path is too long, file object inside: ", path, node
                return None

        path_tags = []
        head, tail = _split(path)
        while tail:
            path_tags.append( tail )
            head, tail = _split( head )
        if head:
            path_tags.append( head )

        selected = walker( self, path_tags )
        if selected:
            self.selected = selected
        else:
            print "Cannot find item for path: ", path, path_tags


    def _selected_changed( self, value ):
        print 'selected', self.selected

    def _enum_items( self ):
        return [
        FolderEntity(
            parent = None, 
            sys_name = name, 
            deferred = False
            )  for name in _enum_root()
        ]


class BookmarksFileStorage(object):
    """
    OS-indepenent storage for filesystem bookmarks.
    """
    def __init__( self, path ):
        self.path = path

    def _raw_load( self ):
        """ Return encoded list """
        items = []
        if _exists(self.path):
            with open(self.path,'rb') as f:
                for row in f:
                    row = row.strip()
                    if len(row) > 0:
                        items.append(row)
        print "loaded", items
        return items

    def update( self, path ):
        """
        Add path to items (if not exists).
        Update underlying file if necessary.
        Return True if items were changed.
        """

        def _encode( path ):
            return path.replace(_sep, ';')

        # encode path, append, sort, store it

        raw_list = self._raw_load()

        indexed_storage = dict([(_path, True) for _path in raw_list])

        # do not add duplicates:

        raw_path = _encode(path)

        print "path", path
        print 'raw_path', raw_path
        print 'raw_list', raw_list

        if raw_path in indexed_storage:
            return False

        raw_list.append( raw_path )
        raw_list.sort(  lambda l, r: cmp( l.lower(), r.lower() ) )

        with open(self.path,'wb') as f:
            f.write("\n".join(raw_list))

        return True

    def items( self ):
        """
        Return stored boormarks as list.
        """
        def _decode( path ):
            return path.replace(';', _sep)

        return [_decode(row) for row in self._raw_load()]


class FileExplorerModel(HasTraits):
    """
    ############################################
    Data model for entire variable explorer
    ############################################
    """
    fs_tree =  Instance(FileSystemTree)

    user_path = Str

    favorites = List

    location = Str

    def __init__(self, **traits):
        HasTraits.__init__(self, **traits)
        self.fs_tree = FileSystemTree()

        self._bookmarks_storage = BookmarksFileStorage(_join(_script_folder(), 'favorites.txt'))
        try:
            self.favorites = self._bookmarks_storage.items()
        except Exception as e:
            print e
            pass

    def _user_path_changed( self, value ):
        print 'My path', self.user_path
        self.fs_tree.path = self.user_path

    def _location_changed( self, value ):
        location = self.location
        if location:
            self.user_path = location

    def add_boormark( self, path ):
        storage = self._bookmarks_storage
        if storage.update( path ):
            self.favorites = storage.items()


# ############################################
#
# Handlers
#
# ############################################

_action_import = Action(name='Import', action='_menu_import')
_action_export = Action(name='Export', action='_menu_export')
_action_info = Action(name='Info', action='_menu_info')
_action_refresh = Action(name='Refresh', action='_menu_refresh')
_action_bookmark = Action(name='Add to favorites', action='_menu_bookmark')


# ############################################
#
# Views
#
# ############################################

# View for objects that aren't edited
no_view = View()

file_entity_details = \
    View(
        Group(
            # Item(
            #     'sys_name',
            #     style='readonly',
            #     show_label=False,
            # ),
            Item(
                'display_tooltip',
                style='readonly',
                show_label=False,
            ),
            orientation='vertical',
            show_left=True,
        )
    )

# TreeEditorEx(

file_tree_editor = \
    TreeEditorEx(
        nodes=[
            ObjectTreeNode(
                node_for  = [FolderEntity],
                children = 'items',
                menu = Menu(
                    _action_bookmark,
                    Separator(),
                    _action_refresh
                ),
                # children = 'children',
                auto_open = False,
                # view = no_view,
                view      = file_entity_details,

            ),
            ObjectTreeNode(
                node_for = [FileEntity],
                menu = Menu(
                    _action_import,
                    _action_export,
                    Separator(),
                    _action_info
                ),
                # children = 'children',
                # auto_open=True,
                view      = file_entity_details,
            ),
        ],
        hide_root = True,
        # depth (in levels) to open initially:
        auto_open = 1,
        # item editors at the bottom:
        orientation='vertical',
        # hide item editors:
        editable = False,
        selected = 'object.fs_tree.selected'
    )


view = View(
    VGroup(
        HGroup(
            Label(' '),
            Item(
                name='location',
                editor = EnumEditor(name = 'favorites'),
                show_label=False,
                tooltip='Favorites'
            ),
            Label(' '),
        ),
        HGroup(
            Label(' '),
            Item(
                name="fs_tree",
                style="custom",
                editor=file_tree_editor,
                show_label=False,
            ),
            Label(' '),
        ),
        HGroup(
            Label(' '),
            Item(
                name='user_path',
                style="custom", 
                editor=TextEditor(auto_set=False, enter_set=True, multi_line=False),
                show_label=False
            ),
            Label(' '),
        ),
    ),
    width=600,
    height=700,
    resizable=False,
    title=u'File Explorer',
)


# ############################################
#
# Controllers
#
# ############################################

class FileExplorer(Controller):
    """docstring for FileExplorerController"""

    event_bus = Instance(EventBus)
    command = DelegatesTo('event_bus')
    args = DelegatesTo('event_bus')

    view = view

    def _menu_info( self, uinfo, object ):
        print "_menu_info", self.__class__, uinfo, object

    def _menu_import( self, uinfo, object ):
        print "Import", object.path
        self.event_bus.fire_event('CMD_IMPORT', object.path)

    def _menu_export( self, uinfo, object ):
        print "Export", object.path
        self.event_bus.fire_event('CMD_EXPORT', object.path)
    
    def _menu_refresh( self, uinfo, object ):
        print "refreshing: ", object
        object.refresh()

    def _menu_bookmark( self, uinfo, object ):
        print "Adding favorite: ", object
        self.model.add_boormark(object.path)


model = FileExplorerModel

if __name__ == '__main__':

    """
    Test mode
    """

    import doctest
    doctest.testmod(verbose=True)

    FileExplorer(
        model=model(
        ),
        event_bus=EventBus()
    ).configure_traits()

