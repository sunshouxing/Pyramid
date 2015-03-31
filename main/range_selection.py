# -*- coding: utf-8 -*-

r""" Defines the RangeSelection and RangeSelectionOverlay class. """

# ---- Imports --------------------------------------------------------------------
from __future__ import with_statement
from numpy import array

# Enthought library imports
from enable.api import ColorTrait, LineStyle
from traits.api import \
    HasTraits, Enum, Float, Property, Bool, Instance, cached_property, on_trait_change
from chaco.api import \
    AbstractOverlay, GridMapper, AbstractMapper


class RangeSelection(HasTraits):
    #---- Trait Definitions-------------------------------------------------------
    # whether the range selection is active or not
    active = Bool

    # the lower bound of range selection
    lower = Float

    # the upper bound of range selection
    upper = Float

    def __init__(self, lower, upper):
        self.active = True
        self.lower = lower
        self.upper = upper

    def __str__(self):
        active = self.active and 1 or 0
        return "Selection:[{}]({}, {})".format(active, self.lower, self.upper)


class RangeSelectionOverlay(AbstractOverlay):
    """ Highlights the selection region on a component. """

    # The axis to which this tool is perpendicular.
    axis = Enum("index", "value")

    # Mapping from screen space to data space. By default, it is just self.component.
    plot = Property(depends_on='component')

    # The mapper (and associated range) that drive this RangeSelectionOverlay.
    # By default, this is the mapper on self.plot that corresponds to self.axis.
    mapper = Instance(AbstractMapper)

    # The element of an (x,y) tuple that corresponds to the axis index.
    # By default, this is set based on self.asix and self.plot.orientation,
    # but it can be overridden and set to 0 or 1.
    axis_index = Property

    # the selected range
    selection = Instance(RangeSelection, (0, 0))

    coordinate = Property(depends_on=['selection.active', 'selection.lower', 'selection.upper'])

    #------------------------------------------------------------------------
    # Appearance traits
    #------------------------------------------------------------------------

    # The color of the selection border line.
    border_color = ColorTrait("dodgerblue")
    # The width, in pixels, of the selection border line.
    border_width = Float(1.0)
    # The line style of the selection border line.
    border_style = LineStyle("solid")
    # The color to fill the selection region.
    fill_color = ColorTrait("lightskyblue")
    # The transparency of the fill color.
    alpha = Float(0.3)

    #------------------------------------------------------------------------
    # AbstractOverlay interface
    #------------------------------------------------------------------------

    def __init__(self, *args, **traits):
        super(RangeSelectionOverlay, self).__init__(*args, **traits)
        self.selection = traits['selection']

    def overlay(self, component, gc, view_bounds=None, mode="normal"):
        """ Draws this component overlaid on another component. Overrides AbstractOverlay. """

        axis_ndx = self.axis_index
        lower_left = [0, 0]
        upper_right = [0, 0]

        for coord in self.coordinate:
            start, end = coord
            lower_left[axis_ndx] = start
            lower_left[1 - axis_ndx] = component.position[1 - axis_ndx]
            upper_right[axis_ndx] = end - start
            upper_right[1 - axis_ndx] = component.bounds[1 - axis_ndx]

            with gc:
                gc.clip_to_rect(component.x, component.y, component.width, component.height)
                gc.set_alpha(self.alpha)
                gc.set_fill_color(self.fill_color_)
                gc.set_stroke_color(self.border_color_)
                gc.set_line_width(self.border_width)
                gc.set_line_dash(self.border_style_)
                gc.draw_rect((lower_left[0], lower_left[1], upper_right[0], upper_right[1]))


    #------------------------------------------------------------------------
    # Private methods
    #------------------------------------------------------------------------
    @on_trait_change("selection.active,selection.lower,selection.upper")
    def selection_changed(self):
        self.plot.request_redraw()

    @cached_property
    def _get_coordinate(self):
        if self.selection.active:
            return [self.mapper.map_screen(array((self.selection.lower, self.selection.upper)))]
        else:
            return []

    def _determine_axis(self):
        """ Determines which element of an (x,y) coordinate tuple corresponds
        to the tool's axis of interest.

        This method is only called if self._axis_index hasn't been set (or is
        None).
        """
        if self.axis == "index":
            if self.plot.orientation == "h":
                return 0
            else:
                return 1
        else:  # self.axis == "value"
            if self.plot.orientation == "h":
                return 1
            else:
                return 0

    #------------------------------------------------------------------------
    # Trait event handlers
    #------------------------------------------------------------------------

    def _component_changed(self, old, new):
        self._attach_metadata_handler(old, new)
        return

    def _axis_changed(self, old, new):
        self._attach_metadata_handler(old, new)
        return

    def _attach_metadata_handler(self, old, new):
        # This is used to attach a listener to the datasource so that when
        # its metadata has been updated, we catch the event and update properly
        if not self.plot:
            return

        data_source = getattr(self.plot, self.axis)
        if old:
            data_source.on_trait_change(self._metadata_change_handler, "metadata_changed", remove=True)
        if new:
            data_source.on_trait_change(self._metadata_change_handler, "metadata_changed")
        return

    def _metadata_change_handler(self, event):
        self.component.request_redraw()
        return

    #------------------------------------------------------------------------
    # Default initializer
    #------------------------------------------------------------------------

    def _mapper_default(self):
        # If the plot's mapper is a GridMapper, return either its
        # x mapper or y mapper

        mapper = getattr(self.plot, self.axis + "_mapper")

        if isinstance(mapper, GridMapper):
            if self.axis == 'index':
                return mapper._xmapper
            else:
                return mapper._ymapper
        else:
            return mapper

    #------------------------------------------------------------------------
    # Property getter/setters
    #------------------------------------------------------------------------

    @cached_property
    def _get_plot(self):
        return self.component

    @cached_property
    def _get_axis_index(self):
        return self._determine_axis()

# EOF
