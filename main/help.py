# -*- coding: utf-8 -*-

# ---- [Imports] --------------------------------------------------------------
from traits.api import SingletonHasTraits, HTML
from traitsui.api import UItem, View, HTMLEditor

# TODO edit help info content
help_text = u"""
<i>Here are some lists formatted in this way:</i>

以数据为中心，来组织。
  * 数据下载
    - 路径：[菜单][工具][数据下载器]
    - 说明：根据用户指定的日期、桥梁、设备、传感器和通道等信息，自动从数据中心下载数据，目前已支持的数据中心包括闵浦二桥和东海大桥。
  * 数据读取
    - 路径：
    - 说明：
  * 数据生成
    - 路径：
    - 说明：
  * 数据导入/导出
    - 路径：
    - 说明：
  * 数据处理
    - 滤波器
      - 路径：
      - 说明：
    - 拟合器
      - 路径：
      - 说明：

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
