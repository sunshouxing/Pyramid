# -*- coding: utf-8 -*-

from os.path import join, isdir
import os

import numpy as np
import pylab as plt

from data_file import create_data_file
from timemodule import DateTime, create_date_time


class Fields(object):
    """搜索文件的条件"""

    def __init__(self, **kwargs):
        # self._root =
        self._path = r'{root}\{datetime:%Y%m%d}\{sensor_channel}'
        self._bridge_station = ''
        self._sensor_channel = []
        self._start_time = DateTime.fromtimestamp(0)
        self._end_time = DateTime.fromtimestamp(0)
        for key in kwargs.keys():
            self.__setattr__(key, kwargs.get(key))

    @property
    def root(self):
        return self._root

    @root.setter
    def root(self, value):
        if isdir(value):
            self._root = value
        else:
            raise ValueError('The value assigned to root field is not a valid directory')

    @property
    def bridge_station(self):
        return self._bridge_station

    @bridge_station.setter
    def bridge_station(self, value):
        if isinstance(value, basestring):
            self._bridge_station = value
        else:
            raise ValueError('Invalid assignment to bridge_station field: strings required')

    @property
    def sensor_channel(self):
        return self._sensor_channel

    @sensor_channel.setter
    def sensor_channel(self, value):
        if isinstance(value, (list, tuple)) and all([isinstance(item, basestring) for item in value]):
            self._sensor_channel = value
        elif isinstance(value, basestring):
            self._sensor_channel = [value]
        else:
            raise ValueError('Invalid assignment to sensor_channel field: string or list of strings required')

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if isinstance(value, (str, unicode)):
            self._path = value
        else:
            raise ValueError('Invalid assignment to path field: strings required')

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, value):
        self._start_time = create_date_time(value)

    @property
    def end_time(self):
        return self._end_time

    @end_time.setter
    def end_time(self, value):
        self._end_time = create_date_time(value)

    @property
    def start_path(self):
        return {sensor_channel: self.path.format(
            root=self.root,
            bridge_station=self.bridge_station,
            sensor_channel=sensor_channel,
            datetime=self.start_time)
            for sensor_channel in self.sensor_channel}

    @property
    def end_path(self):
        return {sensor_channel: self.path.format(
            root=self.root,
            bridge_station=self.bridge_station,
            sensor_channel=sensor_channel,
            datetime=self.end_time)
            for sensor_channel in self.sensor_channel}

    def compare_path(self, path):
        """compare the three paths，return true if each component of "path" was under
        the constraint of the corresponding component of "start_path" and "end_path". """

        # for sensor_channel in self.sensor_channel:
        #
        #     path_components = path.split(os.sep)
        #     start_path_components = self.start_path[sensor_channel].split(os.sep)
        #     end_path_components = self.end_path[sensor_channel].split(os.sep)
        #
        #     path_component_under_constraint = \
        #         [start_path_components[i] <= path_components[i] <= end_path_components[i]
        #          for i in range(len(path_components))]
        #     if all(path_component_under_constraint):
        #         return True
        # else:
        #     return False
        return True

    def compare_file(self, data_file):
        if data_file.sensor_channel not in self.sensor_channel:
            return False
        else:
            if data_file.start_time >= self.end_time:
                return False
            elif data_file.end_time <= self.start_time:
                return False
            else:
                return True


class HistoryData(object):
    def __init__(self, fields):
        self.start_time = fields.start_time
        self.end_time = fields.end_time
        self.history_data = {sensor_channel: None for sensor_channel in fields.sensor_channel}

    def update(self, data_file):

        if self.history_data[data_file.sensor_channel] is None:
            time = np.arange(self.start_time.timestamp(),
                             self.end_time.timestamp(),
                             data_file.dt(), dtype='>u8')
            self.history_data[data_file.sensor_channel] = np.empty(
                time.size, dtype=[('time', '>u8'), ('data', '>f4')])
            self.history_data[data_file.sensor_channel]['time'] = time
            self.history_data[data_file.sensor_channel]['data'].fill(np.NaN)

        time_data = data_file.read()
        # FIXME debug info
        print time_data

        if data_file.start_time < self.start_time:
            time_data = time_data[time_data['time'] >= self.start_time.timestamp()]
        if data_file.end_time > self.end_time:
            time_data = time_data[time_data['time'] < self.end_time.timestamp()]

        start_index = int((time_data['time'][0] - self.start_time.timestamp()) / data_file.dt())
        self.history_data[data_file.sensor_channel][start_index: start_index + len(time_data)] = time_data


def read_data(fields):
    """
    find and read data files according to the information given in 'fields'.

        Syntax:: history_data = read_history_data(fields)
        Input:: fields
            An instance of Class Fields
        Output:: history_data
            The history_data component of Class HistoryData
    """

    history_data = HistoryData(fields)

    for sup_dir, sub_dirs, sub_files in os.walk(fields.root):
        irrelevant_dirs = \
            [sub_dir for sub_dir in sub_dirs if not fields.compare_path(join(sup_dir, sub_dir))]
        for irrelevant_dir in irrelevant_dirs:
            sub_dirs.remove(irrelevant_dir)

        for file_name in sub_files:
            data_file = create_data_file(sup_dir, file_name)
            if data_file is not None and fields.compare_file(data_file) is True:
                # FIXME debug info
                print data_file.file_name
                history_data.update(data_file)

    return history_data.history_data


if __name__ == '__main__':

    # input_dict从界面程序传过来
    input_dict = {
        'root': r'e:\MelakBridge\HistoryData',  # root和“文件根目录”相对应
        'sensor_channel': ('SEW1111-DX', 'SEW1112-DX'),  # sensor_channel和“传感器通道”相对应
        'start_time': '2015-09-01 02:00:00',  # start_time和“开始日期”相对应
        'end_time': '2015-09-03 03:25:00',  # end_time和“结束日期”相对应
    }

    fields = Fields(**input_dict)

    np_history_data = read_data(fields)

    # 程序返回的结果np_history_data是一个dict，
    # 每一个“传感器通道”是一个key，在本例中即np_history_data = {'SWS1101-DS': {}, 'SWS1101-DD':{}}
    # 而每个key对应的值又是一个dict，结构如下{'time':[], 'data':[]}
    key = fields.sensor_channel[1]

    # print np_history_data[key].keys()
    print DateTime.fromtimestamp(np_history_data[key]['time'][0] / 1000)
    print DateTime.fromtimestamp(np_history_data[key]['time'][-1] / 1000)
    plt.plot(np_history_data[key]['time'], np_history_data[key]['data'])
    plt.show()
    print len(np_history_data[key]['data'])

'''
    import sys
    import json

    with open(sys.argv[1], 'r') as json_input_file:
        input_dict = json.load(json_input_file)

    fields = Fields(**input_dict)

    np_history_data = read_history_data(fields)

    key = fields.sensor_channel[1]
    print DateTime.fromtimestamp(np_history_data[key]['time'][0] / 1000)
    print DateTime.fromtimestamp(np_history_data[key]['time'][-1] / 1000)
    plt.plot(np_history_data[key]['time'], np_history_data[key]['data'])
    plt.show()

    history_data = dict()
    for sensor_channel in fields.sensor_channel:
        history_data[sensor_channel] = dict()
        history_data[sensor_channel]['time'] = np_history_data[sensor_channel]['time'].tolist()
        history_data[sensor_channel]['data'] = np_history_data[sensor_channel]['data'].tolist()

    with open(sys.argv[2], 'w') as json_output_file:
        json.dump(history_data, json_output_file)

        # CMD
        # python read_history_data.py json_input_file.txt json_output_file.txt
'''
