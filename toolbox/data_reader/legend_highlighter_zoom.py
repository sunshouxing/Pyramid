__author__ = 'SUN Shouwang'

import operator

from chaco.tools.api import LegendHighlighter


class LegendHighlighterZoom(LegendHighlighter):

    def _set_states(self, plots):
        """ Decorates a plot to indicate it is selected """
        mask_array = None
        max_value = None
        min_value = None
        for render in reduce(operator.add, plots.values()):
            if not hasattr(render, '_orig_alpha'):
                # FIXME: These attributes should be put into the class def.
                render._orig_alpha = render.alpha
                render._orig_line_width = render.line_width
            if render in self._selected_renderers:
                render.line_width = render._orig_line_width * self.line_scale
                render.alpha = render._orig_alpha
            else:
                render.alpha = render._orig_alpha / self.dim_factor
                render.line_width = render._orig_line_width / self.line_scale

            if render in self._selected_renderers:
                if mask_array is None:
                    mask_array = render.container.index_range.mask_data(render.index.get_data())
                if max_value is None:
                    max_value = max(render.value.get_data()[mask_array])
                else:
                    max_value = max(max_value, max(render.value.get_data()[mask_array]))
                if min_value is None:
                    min_value = min(render.value.get_data()[mask_array])
                else:
                    min_value = min(min_value, min(render.value.get_data()[mask_array]))
        range_vallue = max_value - min_value
        render.container.value_range.set_bounds(min_value-range_vallue/10, max_value+range_vallue/10)