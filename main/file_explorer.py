# -*- coding: utf-8 -*-

import os
import os.path as osp
import platform
import time

from traits.api import \
    HasTraits, Bool, Str, Any, Tuple, List, \
    Instance, Property, Event, DelegatesTo, cached_property
from traitsui.api import \
    TextEditor, TreeNodeObject, EnumEditor, ObjectTreeNode, \
    View, UItem, UReadonly, UCustom, \
    Group, HGroup, VGroup, Controller, TreeEditor, Menu, Action, Separator
from traitsui.qt4.tree_editor import SimpleEditor

from common import PROJECT_HOME
from main.book_marks import Bookmarks
from main.event_bus import EventBus


def _script_folder():
    import sys
    return osp.abspath(osp.dirname(sys.argv[0]))


_os_name = platform.system().lower()

if _os_name.startswith('windows'):

    def _enum_root():
        import string
        from ctypes import windll

        drives = []
        bit_mask = windll.kernel32.GetLogicalDrives()
        for letter in string.uppercase:
            if bit_mask & 1:
                drives.append('{}:{}'.format(letter, osp.sep))
            bit_mask >>= 1
        return drives

elif _os_name.startswith('linux'):

    def _enum_root():
        return ['/']

else:
    import sys

    def _enum_root():
        path = _script_folder()
        while osp.split(path)[1]:
            path = osp.split(path)[0]
        return path


def scan_folder(path):
    try:
        return os.listdir(path)
    except:
        return []


class FileExplorerError(Exception):
    """ Generic error in File Explorer """
    pass


class PatchedEditor(SimpleEditor):
    def init(self, parent):
        SimpleEditor.init(self, parent)
        tree_model = self.value
        print "tree_model", tree_model
        tree_model.editor = self

    def _create_item(self, nid, node, entry, index=None):
        """ Create  a new TreeWidgetItem as per word_wrap policy.

        Index is the index of the new node in the parent:
            None implies append the child to the end. """
        cnid = SimpleEditor._create_item(self, nid, node, entry, index)

        # set reference to the toolkit widget:
        # object.deferred = False
        entry.nid = cnid

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
        return "{!s}: {!s} \nModified: {!s}\nSize:{!s} bytes".format(
            self.name, self.sys_name, info['last_modified'], info['size'])

    def _get_path(self):
        """ path = Property """
        return osp.join(self.parent.path, self.sys_name)

    @cached_property
    def _get_info(self):
        """ info = Property """
        try:
            (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(self.path)
            return dict(
                size=str(size),
                last_modified=time.ctime(mtime)
            )
        except Exception as e:
            print 'Exception', e
            return dict(
                size='-',
                last_modified='-'
            )

    def __repr__(self):
        return '<{}; name: {}, path: {}>'.format(self.__class__.__name__, self.sys_name, self.path)

    def refresh(self):
        pass

    def init_items(self):
        pass

    # ---------------------------------------- #
    # Interface / protocol for TreeNodeObject  #
    # ---------------------------------------- #
    def tno_get_label(self, node):
        return self.sys_name

    def tno_get_tooltip(self, node):
        return self.display_tooltip

    def tno_set_label(self, node, label):
        """ Sets the label for a specified object.
        """
        self.sys_name = label

    def tno_get_name(self, node):
        """ Returns the name to use when adding a new object instance
            (displayed in the "New" submenu).
        """
        return self.name

    def tno_get_menu(self, node):
        return node.menu

    def tno_can_auto_open(self, node):
        """ Returns whether the object's children should be automatically
        opened.
        """
        return self.force_expand

    def tno_can_auto_close(self, node):
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
        _, ext = osp.splitext(self.sys_name)
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

    def tno_get_icon(self, node, is_expanded):
        """ Returns the icon for a specified object.
        """
        # Intercept status of this node:
        if not self.visited and is_expanded:
            self.visited = is_expanded

        return FileSystemEntity.tno_get_icon(self, node, is_expanded)

    def _get_path(self):
        if self.sys_name:
            if self.parent is not None:
                return osp.join(self.parent.path, self.sys_name)
            return self.sys_name
        return None

    def _active_child_name_changed(self):
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

    def _force_expand_changed(self):
        if self.nid:
            self.nid.setExpanded(self.force_expand)

    def _visited_changed(self, was_expanded, becomes_expanded):
        if becomes_expanded and not was_expanded:
            # release all chidren to scan items:
            for child in self.items:
                if child.deferred:
                    child.deferred = False

    def _deferred_changed(self, was_deferred, deferred):
        if was_deferred and not deferred:
            self.refresh()

    def refresh(self):
        self.items = []
        self.items = self._enum_items()

    def rebuild(self):
        self._dir_map = {}
        self._file_map = {}
        self.refresh()

    def _enum_items(self):
        """ Gets the object's children.
        """

        dirs = []
        files = []
        path = self.path
        for name in scan_folder(path):
            if name.startswith('.'):
                continue
            cur_path = osp.join(path, name)
            if osp.isdir(cur_path):
                item = self._dir_map.get(name, None)
                if not item:
                    item = FolderEntity(parent=self, sys_name=name)
                    self._dir_map[name] = item
                dirs.append(item)
            elif osp.isfile(cur_path):
                _, ext = osp.splitext(name)
                if ext in self.filter:
                    item = self._file_map.get(name, None)
                    if not item:
                        item = FileEntity(parent=self, sys_name=name)
                        self._file_map[name] = item
                    files.append(item)

        dirs.sort(lambda l, r: cmp(l.sys_name.lower(), r.sys_name.lower()))
        files.sort(lambda l, r: cmp(l.sys_name.lower(), r.sys_name.lower()))

        return dirs + files


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

    def _get_path(self):
        return None

    def _set_path(self, path):
        """ 
        Try to select TreeNode which relates to the path.
        Note: This method does not allow to expand tree to the selected node.
        Reason: Underlying QtTreeWidgetItem with its' .setExpanded(True) is
        hidden inside TreeEditor for qt4 toolkit.
        to-do: try to auto-expand related nodes in a tree view control
        """
        def walker(node, path_tags):
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
                        return walker(item, path_tags)
                    else:
                        return item

                print 'Item "{}" not found in {}'.format(name, node.items)
                return None
            else:
                print "Path is too long, file object inside: ", path, node
                return None

        path_tags = []
        head, tail = osp.split(path)
        while tail:
            path_tags.append(tail)
            head, tail = osp.split(head)
        if head:
            path_tags.append(head)

        selected = walker(self, path_tags)
        if selected:
            self.selected = selected
        else:
            print "Cannot find item for path: ", path, path_tags

    def _enum_items(self):
        return [
            FolderEntity(
                parent=None,
                sys_name=name,
                deferred=False
            ) for name in _enum_root()
        ]


class FileSystem(HasTraits):
    """ Data model for entire variable explorer
    """
    fs_tree = Instance(FileSystemTree)

    user_path = Str

    location = Str

    # bookmarks to provide a shortcut to data directory
    bookmarks = Instance(Bookmarks)
    bookmark_items = DelegatesTo('bookmarks', prefix='items')

    def __init__(self, **traits):
        HasTraits.__init__(self, **traits)
        self.fs_tree = FileSystemTree()
        self.bookmarks = Bookmarks(osp.join(PROJECT_HOME, 'bookmarks.txt'))

    def _user_path_changed(self):
        self.fs_tree.path = self.user_path

    def _location_changed(self):
        location = self.location
        if location:
            self.user_path = location

    def add_bookmark(self, path):
        self.bookmarks.add(path)


# ---- [View definitions] ------------------------------------------------------
_action_import = Action(name=u'导入', action='_menu_import')
_action_export = Action(name=u'导出', action='_menu_export')
_action_info = Action(name=u'信息', action='_menu_info')
_action_refresh = Action(name=u'刷新', action='_menu_refresh')
_action_bookmark = Action(name=u'收藏', action='_menu_bookmark')

no_view = View()

file_entity_details = View(
    VGroup(
        UReadonly('display_tooltip'),
        show_left=True,
    )
)

file_tree_editor = TreeEditorEx(
    nodes=[
        ObjectTreeNode(
            node_for=[FolderEntity],
            children='items',
            menu=Menu(
                _action_bookmark,
                Separator(),
                _action_refresh
            ),
            # children = 'children',
            auto_open=False,
            # view = no_view,
            view=file_entity_details,
        ),
        ObjectTreeNode(
            node_for=[FileEntity],
            menu=Menu(
                _action_import,
                _action_export,
                Separator(),
                _action_info
            ),
            # children = 'children',
            # auto_open=True,
            view=file_entity_details,
        ),
    ],
    hide_root=True,
    # depth (in levels) to open initially:
    auto_open=1,
    # item editors at the bottom:
    orientation='vertical',
    # hide item editors:
    editable=False,
    selected='object.fs_tree.selected'
)


class FileExplorer(Controller):
    """ File explorer used to exchange data with data space.
    """
    tab_name = u'文件浏览器'

    # the event bus between file system and data space
    event_bus = Instance(EventBus)

    traits_view = View(
        HGroup(
            '10',
            VGroup(
                Group(
                    UItem(  # bookmark selection
                        name='location',
                        editor=EnumEditor(name='bookmark_items'),
                    ),
                    show_border=True,
                    label=u'收藏夹',
                ),
                VGroup(
                    UCustom(  # file system directory structure
                        name="fs_tree",
                        editor=file_tree_editor,
                    ),
                    UCustom(  # current path demonstration
                        name='user_path',
                        editor=TextEditor(auto_set=False, enter_set=True, multi_line=False),
                    ),
                    show_border=True,
                    label=u'目录树',
                ),
            ),
            '10',
        ),
        resizable=False,
        title=u'文件浏览器',
    )

    def __init__(self, model, event_bus):
        super(FileExplorer, self).__init__()
        self.model = model
        self.event_bus = event_bus

    # ------------------------------------- #
    #         Menu action handlers          #
    # ------------------------------------- #

    def _menu_info(self, info, object):
        print "_menu_info", self.__class__, info, object

    def _menu_import(self, info, object):
        self.event_bus.fire_event('IMPORT_DATA', object.path)

    def _menu_export(self, info, object):
        self.event_bus.fire_event('EXPORT_DATA', object.path)

    def _menu_refresh(self, info, object):
        object.refresh()

    def _menu_bookmark(self, info, object):
        self.model.add_bookmark(object.path)


file_model = FileSystem

if __name__ == '__main__':
    """
    Test mode
    """

    import doctest

    doctest.testmod(verbose=True)

    FileExplorer(
        model=file_model(),
        event_bus=EventBus()
    ).configure_traits()
