# -*- coding: utf-8 -*-

# --- Imports --------------------------------------------------------------------
from os import walk, getcwd, listdir
from os.path import splitext, join

from traits.api import \
    HasTraits, Directory, Bool, Int, Property, Any, property_depends_on
from traitsui.api import \
    View, VGroup, VSplit, HGroup, Item, CodeEditor, TitleEditor, DNDEditor



# -- Constants ------------------------------------------------------------------
# -- LiveSearch class -----------------------------------------------------------
class LiveSearch(HasTraits):
    # The current root directory being searched:
    root = Directory(getcwd(), entries=10)

    # Should sub directories be included in the search:
    recursive = Bool(True)

    # The live search table filter:
    filter = Property  # Instance( TableFilter )

    # The current list of source files being searched:
    source_files = Property  # List( SourceFile )

    # The currently selected source file:
    selected = Any  # Instance( SourceFile )

    # The contents of the currently selected source file:
    selected_contents = Property  # List( Str )

    # The currently selected match:
    selected_match = Int

    # The text line corresponding to the selected match:
    selected_line = Property  # Int

    # The full name of the currently selected source file:
    selected_full_name = Property  # File

    # The list of marked lines for the currently selected file:
    mark_lines = Property  # List( Int )

    # Summary of current number of files and matches:
    summary = Property  # Str

    # -- Traits UI Views --------------------------------------------------------
    view = View(
        VGroup(
            HGroup(
                Item(
                    'root',
                    id='root',
                    label=u"搜索路径",
                    width=0.5,
                ),
                Item('recursive'),
                show_border=True,
            ),
            VSplit(
                VGroup(
                    Item('summary',
                         editor=TitleEditor()
                    ),
                    dock='horizontal',
                    show_labels=False
                ),
                VGroup(
                    HGroup(
                        Item('selected_full_name',
                             editor=TitleEditor(),
                             springy=True
                        ),
                        Item('selected_full_name',
                             editor=DNDEditor(),
                             tooltip='Drag this file'
                        ),
                        show_labels=False
                    ),
                    Item('selected_contents',
                         style='readonly',
                         editor=CodeEditor(mark_lines='mark_lines',
                                           line='selected_line',
                                           selected_line='selected_line')
                    ),
                    dock='horizontal',
                    show_labels=False
                ),
                id='splitter'
            )
        ),
        title='Live File Search',
        id='enthought.examples.demo.Advanced.'
           'Table_editor_with_live_search_and_cell_editor.LiveSearch',
        width=0.75,
        height=0.67,
        resizable=True
    )

    # -- Property Implementations -----------------------------------------------
    @property_depends_on('search, case_sensitive')
    def _get_filter(self):
        if len(self.search) == 0:
            return lambda x: True

        return lambda x: len(x.matches) > 0

    @property_depends_on('root, recursive, file_type')
    def _get_source_files(self):
        root = self.root
        if root == '':
            root = getcwd()

        file_types = FileTypes[self.file_type]
        if self.recursive:
            result = []
            for dir_path, dir_names, file_names in walk(root):
                for file_name in file_names:
                    if splitext(file_name)[1] in file_types:
                        result.append(SourceFile(
                            live_search=self,
                            full_name=join(dir_path, file_name)))
            return result

        return [SourceFile(live_search=self,
                           full_name=join(root, file_name))
                for file_name in listdir(root)
                if splitext(file_name)[1] in file_types]

    @property_depends_on('selected')
    def _get_selected_contents(self):
        if self.selected is None:
            return ''

        return ''.join(self.selected.contents)

    @property_depends_on('selected')
    def _get_mark_lines(self):
        if self.selected is None:
            return []

        return [int(match.split(':', 1)[0])
                for match in self.selected.matches]

    @property_depends_on('selected, selected_match')
    def _get_selected_line(self):
        selected = self.selected
        if (selected is None) or (len(selected.matches) == 0):
            return 1

        return int(selected.matches[self.selected_match - 1
        ].split(':', 1)[0])

    @property_depends_on('selected')
    def _get_selected_full_name(self):
        if self.selected is None:
            return ''

        return self.selected.full_name

    @property_depends_on('source_files, search, case_sensitive')
    def _get_summary(self):
        source_files = self.source_files
        search = self.search
        if search == '':
            return 'A total of %d files.' % len(source_files)

        files = 0
        matches = 0
        for source_file in source_files:
            n = len(source_file.matches)
            if n > 0:
                files += 1
                matches += n

        return 'A total of %d files with %d files containing %d matches.' % (
            len(source_files), files, matches )

    #-- Traits Event Handlers --------------------------------------------------

    def _selected_changed(self):
        self.selected_match = 1

    def _source_files_changed(self):
        if len(self.source_files) > 0:
            self.selected = self.source_files[0]
        else:
            self.selected = None


if __name__ == '__main__':
    explorer = LiveSearch()
    explorer.configure_traits()
