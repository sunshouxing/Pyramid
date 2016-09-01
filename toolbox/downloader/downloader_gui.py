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

from toolbox.downloader.data_center import DataCenter

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


class Downloader(HasTraits):
    # list of channels which target data generated by
    channels = List(Str)
    # date when target data generated
    date = Date
    # the directory where the downloaded data store
    store_path = Directory

    def __init__(self, *args, **traits):
        super(Downloader, self).__init__(*args, **traits)

        _generate_cookies(USERNAME, PASSWORD)
        self.data_center = DataCenter(USERNAME, PASSWORD)

    def accept_task(self, channel_name):
        if channel_name not in self.channels:
            self.channels.append(channel_name)

    def repeal_task(self, channel_name):
        if channel_name in self.channels:
            self.channels.remove(channel_name)

    def download(self):
        if self.data_center.already_login:
            for src_url, file_name in \
                    self.data_center.collect_download_tasks(self.date.isoformat(), self.channels):
                save_to = os.path.join(self.store_path, file_name)
                _make_dir(os.path.dirname(save_to))
                _download_data(src_url, save_to)


class _Channel(TreeNodeObject):
    # the channel's name
    name = Str('<unknown>')
    # if download this channel's data
    selected = Bool(False)
    # the downloader instance
    downloader = Instance(Downloader)

    def __init__(self, name, downloader):
        super(_Channel, self).__init__()
        self.name = name
        self.downloader = downloader

    def _selected_changed(self):
        if self.selected:
            self.downloader.accept_task(self.name)
        else:
            self.downloader.repeal_task(self.name)

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


class _Sensor(TreeNodeObject):
    # the sensor's name
    name = Str('<unknown>')
    # channels belongs to this sensor
    channels = List(_Channel)
    # list of channel's name
    channel_names = Property
    # selected to download all data of this sensor
    selected = Bool
    # selected to download data of channel in this list
    selected_channels = List(Str)

    def _get_channel_names(self):
        return [channel.name for channel in self.channels]

    def _selected_changed(self):
        for channel in self.channels:
            channel.selected = self.selected

    def _selected_channels_changed(self):
        for channel in [channel for channel in self.channels if channel.name in self.selected_channels]:
            channel.selected = True

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
                    UItem('selected'),
                    enabled_when='len(selected_channels) == 0',
                ),
                VGroup(
                    Label(u'■ 选择下载通道:'),
                    UCustom('selected_channels', editor=CheckListEditor(name='object.channel_names', cols=2)),
                    enabled_when='not selected',
                ),
                label=u'下载方式',
                show_border=True,
            ),
        ),
    )


class _Instrument(TreeNodeObject):
    # the instrument's name
    name = Str('<unknown>')
    # sensors belongs to this instrument
    sensors = List(_Sensor)
    # list of sensors' name
    sensor_names = Property(depends_on='sensors')
    # selected to download all data of this instrument
    selected = Bool
    # selected to download data of sensor in this list
    selected_sensors = List(Str)

    @cached_property
    def _get_sensor_names(self):
        return [sensor.name for sensor in self.sensors]

    def _selected_changed(self):
        for sensor in self.sensors:
            sensor.selected = self.selected

    def _selected_sensors_changed(self):
        for sensor in [sensor for sensor in self.sensors if sensor.name in self.selected_sensors]:
            sensor.selected = True

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
                    UItem('selected'),
                    enabled_when='len(selected_sensors) == 0',
                ),
                VGroup(
                    Label(u'■ 选择下载传感器:'),
                    UCustom('selected_sensors', editor=CheckListEditor(name='object.sensor_names', cols=3)),
                    enabled_when='not selected',
                ),
                label=u'下载方式',
                show_border=True,
            ),
        ),
    )


class _Bridge(TreeNodeObject):
    # the bridge's name
    name = Str('<unknown>')
    # instruments belong to this bridge
    instruments = List(_Instrument)


class DownloaderController(Controller):
    # button to set model's date
    select_date = Button(label=u'时间选择...')
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
        # load bridge details from file
        with open('./sensors_tree.json', 'r') as json_source:
            bridge_detail = json.load(json_source)
        # init bridge field by bridge_detail info
        self.bridge = [_Bridge(
            name=bridge_name,
            instruments=[
                _Instrument(
                    name=instrument_name,
                    sensors=[
                        _Sensor(
                            name=sensor_name,
                            channels=[
                                _Channel(channel_name, self.model) for channel_name in channels
                                ],
                        ) for sensor_name, channels in sensors.items()
                        ],
                ) for instrument_name, sensors in instruments.items()
                ],
        ) for bridge_name, instruments in bridge_detail.items()][0]

    def _select_date_changed(self):
        self.model.edit_traits(view=View(
            UCustom('date'),
            buttons=['OK'],
            title=u'数据生成日期选择',
            kind='panel',
        ))

    def start_download(self, info):
        self.model.download()
        info.ui.control.close()

    bridge_editor = TreeEditor(
        nodes=[
            # The first node specified is the top level one
            ObjectTreeNode(
                node_for=[_Bridge],
                auto_open=True,
                children='instruments',
                label='name',
                view=View(width=600),
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
                # view=no_view,
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
                        UItem('handler.select_date'),
                    ),
                    '10', '_', '10',
                    UItem('handler.bridge', editor=self.bridge_editor),
                    '_',
                    VGroup(
                        UReadonly('channels'),
                        label=u'下载队列',
                    ),
                ),
                '10',
            ),
            buttons=[self.download_button],
            title=u'数据下载器',
            width=850,
            height=900,
            resizable=True,
        )


controller = DownloaderController(Downloader())

if __name__ == '__main__':
    controller.configure_traits()

# EOF