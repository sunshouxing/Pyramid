# -*- coding: utf-8 -*-

# ---- [Imports] --------------------------------------------------------------
from traits.api import SingletonHasTraits, HTML
from traitsui.api import UItem, View, HTMLEditor

# TODO edit help info content
help_text = """
<i>Here are some lists formatted in this way:</i>

Numbered list:
  * first
  * second
  * third

Bulleted list:
  - eat
  - drink
  - be merry
"""


class HelpInfo(SingletonHasTraits):

    # Define a HTML trait to view
    content = HTML(help_text)

    # Demo view
    traits_view = View(
        UItem('content', editor=HTMLEditor(format_text=True)),
        title=u'帮助信息',
        buttons=['OK'],
        width=800,
        height=600,
        resizable=True
    )

# Create the HelpInfo instance:
help_info = HelpInfo()

if __name__ == '__main__':
    help_info.configure_traits()

# EOF
