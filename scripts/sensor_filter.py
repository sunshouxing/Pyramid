# -*- coding: utf-8 -*-

# ---- [Imports] --------------------------------------------------------------
import json

from common import BRIDGES_PATH

if __name__ == '__main__':

    bridge_file = open(BRIDGES_PATH + u'/闵浦二桥.json', 'r')
    bridge_info = json.load(bridge_file)

    for bridge, instruments in bridge_info.items():
        for instrument, sensors in instruments.items():
            for sensor, channels in sensors.items():
                for channel in channels[:]:
                    if channel.find(u'-S') > 0:
                        channels.remove(channel)

    filtered = open(BRIDGES_PATH + u'/filtered.json', 'a')
    print json.dump(bridge_info, filtered, indent=2)

# EOF
