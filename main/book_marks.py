# -*- coding: utf-8 -*-

# ---- [Imports] --------------------------------------------------------------
from traits.api import SingletonHasTraits, Str, List
from traitsui.api import \
    View, Controller, Action, UCustom, HGroup, VGroup, SetEditor

import os.path as osp


class Bookmarks(SingletonHasTraits):

    # book marks already existed
    items = List(Str)

    def __init__(self, path):
        super(Bookmarks, self).__init__()

        self.path = path
        self.items = self.load()

    def load(self):
        """ Load book marks from file
        """
        if osp.exists(self.path):
            with open(self.path, 'rb') as bookmarks:
                return [line.strip().replace(';', osp.sep) for line in bookmarks.readlines()]

    def dump(self):
        """ Dump book marks to file
        """
        with open(self.path, 'w') as storage:
            storage.write('\n'.join([item.replace(osp.sep, ';') for item in self.items]))

    def add(self, path):
        """ Add an path entry to bookmarks
        """
        if path not in self.items:
            self.items.append(path)
            self.dump()


class BookmarksManager(Controller):

    reserved_items = List(Str)

    sync_book_marks = Action(
        id='sync_book_marks_action',
        name=u'完成',
        action='synchronize',
    )

    traits_view = View(
        HGroup(
            '10',
            VGroup(
                UCustom('handler.reserved_items', editor=SetEditor(
                    name='object.items',
                    can_move_all=True,
                    left_column_title=u'当前条目',
                    right_column_title=u'保留条目'
                )),
            ),
            '10',
        ),
        title=u'收藏夹管理',
        buttons=[sync_book_marks],
    )

    def __init__(self, *args, **traits):
        super(BookmarksManager, self).__init__(*args, **traits)

    def synchronize(self, info):
        """ Action handler to synchronize book marks
        """
        info.ui.control.close()
        self.model.items = self.reserved_items
        self.model.dump()
        self.reserved_items = []

# EOF
