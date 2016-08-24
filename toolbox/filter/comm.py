# -*- coding: utf-8 -*-
# from __future__ import absolute_import

# System library imports

# ETS imports
import ConfigParser
import sys

from chaco.api import (DataRange2D, LinearMapper, LogMapper,
                       PlotGrid, PlotAxis)
from chaco.api import Plot, ArrayPlotData
from chaco.scales.api import DefaultScale, LogScale, ScaleSystem
from chaco.scales_tick_generator import ScalesTickGenerator
from traits.api import Any
from traits.api import Font

# import wx
lab_font = Font(u'微软雅黑 12')
color_list = ("0x00ff11", "0x0000ff", "0xffff00", "0x00ff00", "0x00ff99", "0x00aa33", "0xffee16",
              "0xee1399", "0xff31ff", "0x00ffff")

search_path = ["F:/win8/images"]
open_id = 'multi_selection.openfile'
file_name = "F:/aaa.txt"


# def messagebox(caption, text, option=wx.OK | wx.ICON_QUESTION):
#     # app = wx.App(False)
#     dlg = wx.MessageDialog(None, text,
#                            caption, option
#                            )
#     # app.MainLoop()
#     retCode = dlg.ShowModal()
#     dlg.Destroy()
#     return retCode
#
#
# def msgbox(text, option=wx.OK | wx.ICON_QUESTION):
#     return messagebox(u"提示", text, option)


def get_var_type(a):
    str1 = str(type(a))
    return str1.split('\'')[1]
    
def array_pdata_to_dic(arr, xkey, ykey):
    dic = {}
    dic[xkey] = arr.get_data("x")
    dic[ykey] = arr.get_data("y")
    return dic


def dic_to_array_pdata(dic, xkey, ykey):
    x = dic[xkey]
    y = dic[ykey]
    return ArrayPlotData(x=x, y=y)


def data_to_main(data, data1):
    """ Generate simulate data for this demo """
    x = data.get_data("x")
    y = data.get_data("y")
    y1 = data1.get_data("y")
    return ArrayPlotData(x=x, y=y, y1=y1)


def RGBSTR(r, g, b):
    return "0x" + str(b) + str(g) + str(r)


def clear_List(list):
    while len(list) > 0:
        list.pop()



class Ini_File:
    def __init__(self, path):
        self.path = path
        self.cf = ConfigParser.ConfigParser()
        self.cf.read(self.path)

    def get(self, field, key):
        result = ""
        try:
            result = self.cf.get(field, key)
        except:
            result = ""
        return result

    def set(self, field, key, value):
        try:
            self.cf.set(field, key, value)
            self.cf.write(open(self.path, 'w'))
        except:
            return False
        return True


def read_config(config_file_path, field, key):
    cf = ConfigParser.ConfigParser()
    try:
        cf.read(config_file_path)
        result = cf.get(field, key)
    except:
        sys.exit(1)
    return result


def write_config(config_file_path, field, key, value):
    cf = ConfigParser.ConfigParser()
    try:
        cf.read(config_file_path)
        cf.set(field, key, value)
        cf.write(open(config_file_path, 'w'))
    except:
        sys.exit(1)
    return True

main_config = Ini_File("d:/config.ini")


# class CheckboxRenderer(TableDelegate):
#     """ A renderer which displays a checked-box for a True value and an
#         unchecked box for a false value.
#     """
#
#     # ---------------------------------------------------------------------------
#     #  QAbstractItemDelegate interface
#     # ---------------------------------------------------------------------------
#
#     def editorEvent(self, event, model, option, index):
#         """ Reimplemented to handle mouse button clicks.
#         """
#         if event.type() == QtCore.QEvent.MouseButtonRelease and \
#                         event.button() == QtCore.Qt.LeftButton:
#             column = index.model()._editor.columns[index.column()]
#             obj = index.data(QtCore.Qt.UserRole)
#             checked = bool(column.get_raw_value(obj))
#             column.set_value(obj, not checked)
#             return True
#         else:
#             return False
#
#     def paint(self, painter, option, index):
#         """ Reimplemented to paint the checkbox.
#         """
#         # Determine whether the checkbox is check or unchecked
#         column = index.model()._editor.columns[index.column()]
#         obj = index.data(QtCore.Qt.UserRole)
#         checked = column.get_raw_value(obj)
#
#         # First draw the background
#         painter.save()
#         row_brushes = [option.palette.base(), option.palette.alternateBase()]
#         if option.state & QtGui.QStyle.State_Selected:
#             if option.state & QtGui.QStyle.State_Active:
#                 color_group = QtGui.QPalette.Active
#             else:
#                 color_group = QtGui.QPalette.Inactive
#             bg_brush = option.palette.brush(color_group,
#                                             QtGui.QPalette.Highlight)
#         else:
#             bg_brush = index.data(QtCore.Qt.BackgroundRole)
#             if bg_brush == NotImplemented or bg_brush is None:
#                 if index.model()._editor.factory.alternate_bg_color:
#                     bg_brush = row_brushes[index.row() % 2]
#                 else:
#                     bg_brush = row_brushes[0]
#         painter.fillRect(option.rect, bg_brush)
#
#         # Then draw the checkbox
#         style = QtGui.QApplication.instance().style()
#         box = QtGui.QStyleOptionButton()
#         box.palette = option.palette
#
#         # Align the checkbox appropriately.
#         box.rect = option.rect
#         size = style.sizeFromContents(QtGui.QStyle.CT_CheckBox, box,
#                                       QtCore.QSize(), None)
#         box.rect.setWidth(size.width())
#         margin = style.pixelMetric(QtGui.QStyle.PM_ButtonMargin, box)
#         alignment = column.horizontal_alignment
#         if alignment == 'left':
#             box.rect.setLeft(option.rect.left() + margin)
#         elif alignment == 'right':
#             box.rect.setLeft(option.rect.right() - size.width() - margin)
#         else:
#             # FIXME: I don't know why I need the 2 pixels, but I do.
#             box.rect.setLeft(option.rect.left() + option.rect.width() // 2 -
#                              size.width() // 2 + margin - 2)
#
#         box.state = QtGui.QStyle.State_Enabled
#         if checked:
#             box.state |= QtGui.QStyle.State_On
#         else:
#             box.state |= QtGui.QStyle.State_Off
#         style.drawControl(QtGui.QStyle.CE_CheckBox, box, painter)
#         painter.restore()
#
#     def sizeHint(self, option, index):
#         """ Reimplemented to provide size hint based on a checkbox
#         """
#         box = QtGui.QStyleOptionButton()
#         style = QtGui.QApplication.instance().style()
#         return style.sizeFromContents(QtGui.QStyle.CT_CheckBox, box,
#                                       QtCore.QSize(), None)


# class CheckboxColumn(ObjectColumn):
#     # ---------------------------------------------------------------------------
#     #  Initializes the object:
#     # ---------------------------------------------------------------------------
#
#     def __init__(self, **traits):
#         """ Initializes the object.
#         """
#         super(CheckboxColumn, self).__init__(**traits)
#
#         # force the renderer to be a checkbox renderer
#         self.renderer = CheckboxRenderer()
#
#     # ---------------------------------------------------------------------------
#     #  Returns the cell background color for the column for a specified object:
#     # ---------------------------------------------------------------------------
#
#     def get_cell_color(self, object):
#         """ Returns the cell background color for the column for a specified
#             object.
#         """
#
#         # Override the parent class to ALWAYS provide the standard color:
#         return self.cell_color_
#
#     # ---------------------------------------------------------------------------
#     #  Returns whether the column is editable for a specified object:
#     # ---------------------------------------------------------------------------
#
#     def is_editable(self, object):
#         """ Returns whether the column is editable for a specified object.
#         """
#
#         # Although a checkbox column is always editable, we return this
#         # to keep a standard editor from appearing. The editing is handled
#         # in the renderer's handlers.
#         return False


""" A Plot which uses ScaleSystems for its ticks.
"""


def add_default_axes(plot, orientation="normal", vtitle=u"", htitle=u""):
    """
    Creates left and bottom axes for a plot.  Assumes that the index is
    horizontal and value is vertical by default; set orientation to
    something other than "normal" if they are flipped.
    """

    if orientation in ("normal", "h"):
        v_mapper = plot.value_mapper
        h_mapper = plot.index_mapper
    else:
        v_mapper = plot.index_mapper
        h_mapper = plot.value_mapper

    yticks = ScalesTickGenerator()
    left = PlotAxis(
        orientation='left',
        title=vtitle,
        mapper=v_mapper,
        component=plot,
        tick_generator=yticks,
    )

    xticks = ScalesTickGenerator()
    bottom = PlotAxis(
        orientation='bottom',
        title=htitle,
        mapper=h_mapper,
        component=plot,
        tick_generator=xticks,
    )

    plot.underlays.append(left)
    plot.underlays.append(bottom)
    return left, bottom


class ScalyPlot(Plot):
    x_axis = Any()
    y_axis = Any()
    x_ticks = Any()
    y_ticks = Any()
    linear_scale_factory = Any()
    log_scale_factory = Any()

    def _linear_scale_default(self):
        return self._make_scale("linear")

    def _log_scale_default(self):
        return self._make_scale("log")

    def _make_scale(self, scale_type="linear"):
        """ Returns a new linear or log scale """
        if scale_type == "linear":
            if self.linear_scale_factory is not None:
                return self.linear_scale_factory()
            else:
                return ScaleSystem(DefaultScale())
        else:
            if self.log_scale_factory is not None:
                return self.log_scale_factory()
            else:
                return ScaleSystem(LogScale())

    def _init_components(self):
        # Since this is called after the HasTraits constructor, we have to make
        # sure that we don't blow away any components that the caller may have
        # already set.

        if self.range2d is None:
            self.range2d = DataRange2D()

        if self.index_mapper is None:
            if self.index_scale == "linear":
                imap = LinearMapper(range=self.range2d.x_range)
            else:
                imap = LogMapper(range=self.range2d.x_range)
            self.index_mapper = imap

        if self.value_mapper is None:
            if self.value_scale == "linear":
                vmap = LinearMapper(range=self.range2d.y_range)
            else:
                vmap = LogMapper(range=self.range2d.y_range)
            self.value_mapper = vmap

        if self.x_ticks is None:
            self.x_ticks = ScalesTickGenerator(scale=self._make_scale(self.index_scale))
        if self.y_ticks is None:
            self.y_ticks = ScalesTickGenerator(scale=self._make_scale(self.value_scale))

        if self.x_grid is None:
            self.x_grid = PlotGrid(mapper=self.x_mapper, orientation="vertical",
                                   line_color="lightgray", line_style="dot",
                                   component=self, tick_generator=self.x_ticks)
        if self.y_grid is None:
            self.y_grid = PlotGrid(mapper=self.y_mapper, orientation="horizontal",
                                   line_color="lightgray", line_style="dot",
                                   component=self, tick_generator=self.y_ticks)
        if self.x_axis is None:
            self.x_axis = PlotAxis(mapper=self.x_mapper, orientation="bottom",
                                   component=self, tick_generator=self.x_ticks)
        if self.y_axis is None:
            self.y_axis = PlotAxis(mapper=self.y_mapper, orientation="left",
                                   component=self, tick_generator=self.y_ticks)

    def _index_scale_changed(self, old, new):
        Plot._index_scale_changed(self, old, new)
        # Now adjust the ScaleSystems.
        self.x_ticks.scale = self._make_scale(self.index_scale)

    def _value_scale_changed(self, old, new):
        Plot._value_scale_changed(self, old, new)
        # Now adjust the ScaleSystems.
        self.y_ticks.scale = self._make_scale(self.value_scale)
