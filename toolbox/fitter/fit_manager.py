# -*- coding: utf-8 -*-

# ---- [Imports] --------------------------------------------------------------
try:
    import cPickle as pickle
except ImportError:
    import pickle

from pyface.api import FileDialog, OK
from traits.api import SingletonHasTraits, List
from traitsui.api import View, Controller, UItem, Readonly, Group, \
    TableEditor, ObjectColumn, Menu, Action, Separator
from traitsui.extras.checkbox_column import CheckboxColumn

from toolbox.fitter.fit import Fit


class FitColumn(ObjectColumn):
    style = 'readonly'

    def get_text_color(self, fit):
        return ['light grey', 'black'][fit.selected]

table_editor = TableEditor(
    columns=[
        CheckboxColumn(name='selected', width=0.12),
        FitColumn(name='name', width=0.20),
        FitColumn(name='type', width=0.20),
        FitColumn(name='loc', width=0.10, horizontal_alignment='center'),
        FitColumn(name='scale', width=0.20),
    ],
    menu=Menu(
        Action(
            id='fit_manager_select_all',
            name=u'全选',
            action='_menu_select_all',
            enabled_when='len(object.fits)>1'
        ),
        Separator(),
        Action(
            id='fit_manager_import',
            name=u'导入...',
            action='_menu_import'
        ),
        Action(
            id='fit_manager_export_selected',
            name=u'导出选中...',
            action='_menu_export_selected',
            enabled_when='len(object.fits)>0'
        ),
        Action(
            id='fit_manager_export_all',
            name=u'导出全部...',
            action='_menu_export_all',
            enabled_when='len(fits)>0'
        ),
        Separator(),
        Action(
            id='fit_manager_delete_selected',
            name=u'删除选中',
            action='_menu_delete_selected',
            enabled_when='len(fits)==3'
        ),
        Action(
            id='fit_manager_delete_all',
            name=u'删除全部',
            action='_menu_delete_all',
            # enabled_when='len(object.fits)==3'
        ),
    ),
    edit_view=View(
        Group(
            Readonly('name'),
            Readonly('loc'),
            Readonly('scale'),
            Readonly(
                'shapes_desc',
                label='Shapes',
                visible_when='len(shapes)'
            ),
            show_border=True
        ),
        resizable=True
    ),
    deletable=True,
    sort_model=True,
    auto_size=True,
    orientation='vertical',
    show_toolbar=True,
    row_factory=Fit,
)


class Fits(SingletonHasTraits):
    fits = List(Fit)


class FitManager(Controller):

    traits_view = View(
        Group(
            UItem('fits', editor=table_editor),
            show_border=True,
        ),
        title=u'拟合管理器',
        width=600,
        resizable=True,
        kind='live',
    )

    def __init__(self):
        super(FitManager, self).__init__(model=Fits())

    def _menu_select_all(self, info, selection):
        for fit in self.model.fits:
            fit.selected = True

    def _menu_delete_selected(self, info, selection):
        wanna_delete = [fit for fit in self.model.fits if fit.selected]
        for fit in wanna_delete:
            self.model.fits.remove(fit)

    def _menu_delete_all(self, info, selection):
        while len(self.model.fits) > 0:
            self.model.fits.pop()

    def _menu_import(self, ui_info, selection):
        dialog = FileDialog(
            parent=ui_info.ui.control,
            action='open',
            wildcard="PICKLE files (*.pickle)|*.pickle",
        )
        if dialog.open() == OK:
            with open(dialog.path, 'rb') as load_file:
                while True:
                    try:
                        fit = pickle.load(load_file)
                    except EOFError:
                        break
                    else:
                        # print fit.name, fit.loc, fit.scale, fit.type, fit.distribution
                        if fit is not None:
                            self.model.fits.append(fit)

    def _menu_export_all(self, info, selection):
        dialog = FileDialog(
            parent=info.ui.control,
            action='save as',
            wildcard="PICKLE files (*.pickle)|*.pickle",
        )
        if dialog.open() == OK:
            with open(dialog.path, 'wb') as dump_file:
                for fit in self.model.fits:
                    pickle.dump(fit, dump_file)

    def _menu_export_selected(self, info, selection):
        dialog = FileDialog(
            parent=info.ui.control,
            action='save as',
            wildcard="PICKLE files (*.pickle)|*.pickle",
        )
        if dialog.open() == OK:
            with open(dialog.path, 'wb') as dump_file:
                for fit in self.model.fits:
                    if fit.selected:
                        pickle.dump(fit, dump_file)

if __name__ == '__main__':
    try:
        FitManager().configure_traits()
    except AttributeError:
        pass

# EOF
