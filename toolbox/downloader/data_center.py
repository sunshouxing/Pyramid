# -*- coding: utf-8 -*-

# ---- Imports ---------------------------------------------------------------------------
import urllib
import urllib2
import cookielib
import logging
import json
import re
import os

from xml.dom import minidom
from urllib2 import URLError, HTTPError, HTTPCookieProcessor
import urlparse
import datetime
import subprocess

# # "这是一个传感器数据查询链接"
# # TARGET_URL = "http://mpeqhealth.shgltz.com/web/m/m04/channel-data-file!list?channelCode=SWS0601-DS"
#
# # "打包下载"
#
# # "sensor data file query url"
# SENSOR_DATA_QUERY_URL = "http://mpeqhealth.shgltz.com/web/m/m04/channel-data-file!list?channelCode=SGP0301-S8"
#
# TREE_NODE_URL = "http://mpeqhealth.shgltz.com/web/m/m04/channel-data-file-tree!treedata?treetype=type"
# # TARGET_URL = "http://mpeqhealth.shgltz.com/web/m/m04/channel-data-file-tree-choose"


def parse_with_json(content):
    # standardize the content first
    regex = re.compile(r"\b([a-z]*)\b:")
    content = regex.sub(r'"\1":', content).replace("'", '"')

    return json.loads(content)


class DataCenter():
    """
    DataCenter是上海闵浦二桥结构健康监测系统--数据中心的一个抽象，用户可以使用它来进行登录认证，
    查询数据连接地址以及自动下载数据。
    """

    MAIN_PAGE = "http://mpeqhealth.shgltz.com/web/"
    TREE_NODE_URL = MAIN_PAGE + "m/m04/channel-data-file-tree!treedata?treetype=type"
    DATA_QUERY_URL_TEMPLATE = MAIN_PAGE + "m/m04/channel-data-file-grid!griddataByDay?channelCode={}&day={}"
    DATA_DOWNLOAD_URL_TEMPLATE = MAIN_PAGE + "m/m04/channel-data-file!downloadall?downloadType=pack&ids={}"

    def __init__(self, username, password):
        self.username = username
        self.password = password

        self.already_login = False

        # used as POST info in detect sub nodes request
        self.icons = [
            "/web/themes/default/images/icons/tree_doc.gif",
            "/web/themes/default/images/icons/componenttypeblue.gif",
            "/web/themes/default/images/icons/contract.gif",
            "/web/themes/default/images/icons/office_supplies.gif",
            "/web/themes/default/images/icons/qbs_subbid1.gif",
            "/web/themes/default/images/icons/tree_ssjc_td.gif",
            "/web/themes/default/images/icons/flow.gif"
        ]

        # load sensors from file, sensors are detected by detect_sensors
        # method and store in file prior.
        with open("./sensors.json", "r") as sensors_file:
            self.sensors = json.load(sensors_file)

        # used as the root node when detecting sensors
        self.sensors_root_node = {
            "text": u"传感器设备",
            "leaf": False,
            "id": "device-type|<3000>",
            "icon": self.icons[3],
        }

        # setup client cookie
        self.cookie = cookielib.LWPCookieJar()
        opener = urllib2.build_opener(HTTPCookieProcessor(self.cookie))
        urllib2.install_opener(opener)

        # try to login the data center
        self.login(self.username, self.password)

    @staticmethod
    def get_response_content(request):
        """
        Send the request to server and retrieve the response from server.
        :param request: The request object
        :return: The content of response, None when error
        """
        try:
            response = urllib2.urlopen(request)
        except URLError as error:
            logging.error("URL Error -- message: %s.", error.reason)
            return None
        else:
            content = response.read()
            response.close()
            return content

    def login(self, username, password):
        login_info = urllib.urlencode({'loginname': username, 'loginpass': password})
        login_url = urlparse.urljoin(DataCenter.MAIN_PAGE, 'logon')

        request = urllib2.Request(login_url, login_info, {"Connection": "keep-alive"})
        content = self.get_response_content(request)

        if content:
            self.already_login = True

            # the save() method won’t save session cookies anyway, unless
            # you ask otherwise by passing a true ignore_discard argument.
            # self.cookie.save("cookies.txt", ignore_discard=True)
            logging.info("You have successfully logged into the data center.")
        else:
            logging.error("Failed to login, please ensure you have already been online"
                          " and check the your username and password.")

    def detect_sub_nodes(self, node):
        post_info = urllib.urlencode({'id': node["id"], 'imageUrl': self.icons[:], 'node': node["id"]}, doseq=True)
        request = urllib2.Request(self.TREE_NODE_URL, post_info)

        content = self.get_response_content(request)
        if content:
            return parse_with_json(content)
        else:
            return []

    def detect_sensors(self, node):
        """
        Detect all the sensors in this data center's collection.
        :param node: The root node of sensors navigation tree
        :return: All of the sensor nodes
        """
        if node["leaf"]:
            self.sensors.append(node)
        else:
            sub_nodes = self.detect_sub_nodes(node)
            for sub_node in sub_nodes:
                self.detect_sensors(sub_node)

    def search_data_files(self, sensor, date):
        """
        Search data files for given sensor in the data center, and the
        date parameter specify the date in which data files generated.
        :param sensor: The sensor's name to be searched
        :param date: The date in which data files generated
        :return: The list of files' id
        """
        url = DataCenter.DATA_QUERY_URL_TEMPLATE.format(sensor, date)
        query_info = urllib.urlencode({
            "start": "0",
            "limit": "200",
            "columns": "id,filename,filesize,starttime,endtime,datacount,filestatus",
            "condition": ""
        })
        request = urllib2.Request(url, query_info)
        content = self.get_response_content(request)

        if content:
            dom_tree = minidom.parseString(content)
            collection = dom_tree.documentElement
            elements = collection.getElementsByTagName("id")
            file_ids = [element.childNodes[0].data for element in elements]

            if not file_ids:
                logging.info("No data file generated for %s in day %s.", sensor, date)
        else:
            logging.error("Error when searching data files for %s in day %s.", sensor, date)
            file_ids = []

        return file_ids

    def collect_download_tasks(self, date, channels=None):
        if channels is None:
            channels = self.sensors

        for channel in channels:
            file_ids = self.search_data_files(channel, date)
            if file_ids:
                src_url = DataCenter.DATA_DOWNLOAD_URL_TEMPLATE.format(",".join(file_ids))
                dst_file = os.path.join(date, channel + ".ZIP")
                yield src_url, dst_file

# EOF
