# -*- coding: utf-8 -*-

# ---- Imports -----------------------------------------------------------
import os
import sys
import json
import urllib
import logging
import subprocess

from traits.api import *
from traitsui.api import *
from pyface.api import ImageResource
from common import BRIDGES_PATH, ICONS_PATH

from toolbox.downloader.data_center import DataCenter

# decide system encoding by platform
if sys.platform.startswith('win'):
    system_encoding = 'gbk'
else:
    system_encoding = 'utf-8'

# username and password used by data center
USERNAME = "sun_lm"
PASSWORD = "sunlimin719"


def _make_dir(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def _download_data(src_url, dst_file):
    """
    Download data specified by src_url with wget, and store data in dst_file.
    :param src_url: The data's url.
    :param dst_file: The file to store data.
    """
    try:
        subprocess.check_call([
            "wget", "--load-cookies=cookies.txt", "--tries=2", "-O", dst_file, src_url
        ])
    except subprocess.CalledProcessError as process_error:
        print("ERROR: {}".format(process_error))
        logging.error("Failed to download data file. Data url: %s.", src_url)


def _generate_cookies(username, password):
    login_info = urllib.urlencode({'loginname': username, 'loginpass': password})
    try:
        subprocess.check_call([
            "wget", "--output-document=logon",
            "--post-data=" + login_info,
            "--keep-session-cookies", "--save-cookies=cookies.txt",
            "http://mpeqhealth.shgltz.com/web/logon"
        ])
    except subprocess.CalledProcessError as process_error:
        print("ERROR: {}".format(process_error))
        logging.error("Failed to generate wget cookie.")
        sys.exit(-1)





class _Channel(BridgeTreeNode):

    # --------------------------------------------------------------------
    # Traits View Definition
    # --------------------------------------------------------------------
    traits_view = View(
        VGroup(
            Group(
                UReadonly('name'),
                label=u'通道信息',
                show_border=True,
            ),
            VGroup(
                HGroup(
                    Label(u'下载确认:'),
                    UItem('selected'),
                ),
                label=u'数据下载',
                show_border=True,
            ),
        ),
    )


class _Sensor(BridgeTreeNode):

    # --------------------------------------------------------------------
    # Traits View Definition
    # --------------------------------------------------------------------
    traits_view = View(
        VGroup(
            Group(
                UReadonly('name'),
                label=u'传感器信息',
                show_border=True,
            ),
            VGroup(
                HGroup(
                    Label(u'■ 下载全部:'),
                    UItem('select_all'),
                ),
                VGroup(
                    Label(u'■ 选择下载通道:'),
                    UCustom('selected_children', editor=CheckListEditor(name='object.children_names', cols=2)),
                ),
                label=u'下载方式',
                show_border=True,
            ),
        ),
    )


class _Instrument(BridgeTreeNode):

    # --------------------------------------------------------------------
    # Traits View Definition
    # --------------------------------------------------------------------
    traits_view = View(
        VGroup(
            Group(
                UReadonly('name'),
                label=u'设备信息',
                show_border=True,
            ),
            VGroup(
                HGroup(
                    Label(u'■ 下载全部:'),
                    UItem('select_all'),
                ),
                VGroup(
                    Label(u'■ 选择下载传感器:'),
                    UCustom('selected_children', editor=CheckListEditor(name='object.children_names', cols=3)),
                ),
                label=u'下载方式',
                show_border=True,
            ),
        ),
    )


class _Bridge(TreeNodeObject):

    # --------------------------------------------------------------------
    # Traits View Definition
    # --------------------------------------------------------------------
    traits_view = View(
        VGroup(
            Group(
                UReadonly('name'),
                label=u'桥梁信息',
                show_border=True,
            ),
            VGroup(
                HGroup(
                    Label(u'■ 下载全部:'),
                    UItem('select_all'),
                ),
                VGroup(
                    Label(u'■ 选择下载设备:'),
                    UCustom('selected_children', editor=CheckListEditor(name='object.children_names', cols=3)),
                ),
                label=u'下载方式',
                show_border=True,
            ),
        ),
    )


class DownloaderController(Controller):
    # button to set model's date
    select_date = Button(image=ImageResource('Calendar.png', search_path=[ICONS_PATH]))

    # all bridges where to download data
    bridges = List(Unicode)

    # selected bridge's name
    selected_bridge = Unicode

    # the bridge where data come from
    bridge = Instance(_Bridge)

    # action definition of begin to download
    download_button = Action(
        id='downloader_start_button',
        name=u'开始下载',
        action='start_download',
        enabled_when='object.date and object.store_path and object.channels',
    )

    def __init__(self, *args, **traits):
        super(DownloaderController, self).__init__(*args, **traits)
        # generate candidate bridges' name
        self.bridges = [unicode(_file.split('.')[0], encoding=system_encoding)
                        for _file in os.listdir(BRIDGES_PATH)]

        # init default bridge info
        self.selected_bridge = self.bridges[0]
        bridge_desc_file = os.path.join(BRIDGES_PATH, self.selected_bridge + u'.json')
        self.bridge = self.load_bridge_info(bridge_desc_file)

    def _select_date_changed(self):
        self.model.edit_traits(view=View(
            UCustom('date'),
            buttons=['OK'],
            title=u'数据生成日期选择',
            kind='panel',
        ))

    def _selected_bridge_changed(self):
        bridge_desc_file = os.path.join(BRIDGES_PATH, self.selected_bridge + u'.json')
        self.bridge = self.load_bridge_info(bridge_desc_file)
        self.channels = [channel for instrument in self.bridge
                         for sensor in instrument.sensors
                         for channel in sensor.channels]

    def load_bridge_info(self, desc_file):
        """ Construct a _Bridge object by info loaded from desc_file
        """
        # TODO reload bridge info from cache
        with open(desc_file, 'r') as json_source:
            bridge_detail = json.load(json_source)

        # init bridge field by bridge_detail info
        return [_Bridge(
            name=bridge_name,
            children=[
                _Instrument(
                    name=instrument_name,
                    children=[
                        _Sensor(
                            name=sensor_name,
                            children=[
                                _Channel(channel_name, children=[]) for channel_name in channels
                            ]) for sensor_name, channels in sensors.items()
                    ]) for instrument_name, sensors in instruments.items()
            ]) for bridge_name, instruments in bridge_detail.items()][0]

    def start_download(self, info):
        self.model.download()
        info.ui.control.close()

    bridge_editor = TreeEditor(
        nodes=[
            ObjectTreeNode(
                node_for=[_Bridge],
                auto_open=True,
                children='children',
                label='name',
            ),
            ObjectTreeNode(
                node_for=[_Instrument],
                auto_open=False,
                children='sensors',
                label='name',
                menu=False,
            ),
            ObjectTreeNode(
                node_for=[_Sensor],
                auto_open=False,
                children='channels',
                label='name',
                menu=False,
            ),
            ObjectTreeNode(
                node_for=[_Channel],
                auto_open=False,
                label='name',
            )
        ],
    )

    def traits_view(self):
        return View(
            HGroup(
                '10',
                VGroup(
                    HGroup(
                        Item('store_path', label=u'存储路径'),
                        '_',
                        UCustom('handler.select_date', tooltip=u'时间选择'),
                    ),
                    '10', '_', '10',
                    Item(
                        'handler.selected_bridge',
                        editor=CheckListEditor(values=self.bridges),
                        label=u'桥梁选择',
                    ),
                    UItem('handler.bridge', editor=self.bridge_editor),
                ),
                '10', '_', '10',
            ),
            buttons=[self.download_button],
            title=u'数据下载器',
            width=0.5,
            height=0.6,
            resizable=True,
        )


class Downloader(HasTraits):
    # list of channels which target data generated by
    channels = List(_Channel)
    # date when target data generated
    date = Date
    # the directory where the downloaded data store
    store_path = Directory

    data_center = Any

    def __init__(self, *args, **traits):
        super(Downloader, self).__init__(*args, **traits)

        # _generate_cookies(USERNAME, PASSWORD)
        # self.data_center = DataCenter(USERNAME, PASSWORD)

    def accept_task(self, channel):
        if channel not in self.channels:
            self.channels.append(channel)

    def repeal_task(self, channel):
        if channel in self.channels:
            self.channels.remove(channel)

    def download(self):
        _generate_cookies(USERNAME, PASSWORD)
        self.data_center = DataCenter(USERNAME, PASSWORD)

        if self.data_center.already_login:
            for src_url, file_name in \
                    self.data_center.collect_download_tasks(self.date.isoformat(), self.channels):
                save_to = os.path.join(self.store_path, file_name)
                _make_dir(os.path.dirname(save_to))
                _download_data(src_url, save_to)

controller = DownloaderController(Downloader())

if __name__ == '__main__':
    controller.configure_traits()

# EOF
