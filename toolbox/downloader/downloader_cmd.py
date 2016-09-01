# -*- coding: utf-8 -*-

# ---- Imports ---------------------------------------------------------------------------
import os
import sys
import urllib
import logging
import subprocess
from datetime import date, timedelta

from data_center import DataCenter


def init_logging():
    filename = "downloader.log"
    format = "[%(asctime)-15s:%(levelname)s]:%(message)s"
    logging.basicConfig(filename=filename, level=logging.DEBUG, format=format)


def make_dir(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def download_data(src_url, dst_file):
    """
    Download data specified by src_url with wget, and store data in dst_file.
    :param src_url: The data's url.
    :param dst_file: The file to store data.
    """
    try:
        subprocess.check_call([
            "wget", "--load-cookies=cookies.txt", "--tries=2", "-O", dst_file, src_url
        ])
    except subprocess.CalledProcessError as error:
        print "Error", error
        logging.error("Failed to download data file. Data url: %s.", src_url)


def generate_cookies(username, password):
    login_info = urllib.urlencode({'loginname': username, 'loginpass': password})
    try:
        subprocess.check_call([
            "wget", "--output-document=logon",
            "--post-data=" + login_info,
            "--keep-session-cookies", "--save-cookies=cookies.txt",
            "http://mpeqhealth.shgltz.com/web/logon"
        ])
    except subprocess.CalledProcessError as error:
        print "Error", error
        logging.error("Failed to generate wget cookie.")
        sys.exit(-1)

# username and password used by this data center
USERNAME = "sun_lm"
PASSWORD = "sunlimin719"

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)

if __name__ == "__main__":
    init_logging()
    make_dir(YESTERDAY.isoformat())

    logging.info("========= Begin to download sensor data in date %s =========", YESTERDAY)

    generate_cookies(USERNAME, PASSWORD)
    data_center = DataCenter(USERNAME, PASSWORD)

    if data_center.already_login:
        for src_url, dst_file in data_center.collect_download_tasks(YESTERDAY.isoformat()):
            download_data(src_url, dst_file)

    logging.info("========= Finish to download sensor data in date %s ==========", YESTERDAY)
