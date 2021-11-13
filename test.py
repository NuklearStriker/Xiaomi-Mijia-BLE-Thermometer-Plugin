#!/usr/bin/env python3
#
#   Xiaomi-Mijia-BLE-Thermometer - Domoticz Python plugin
#   LECLERCQ Kevin
#
try:
    import Domoticz
except ImportError:
    import fakeDomoticz as Domoticz

import os
import blescan
import sys
import json

devices = json.loads(str('{"a4:c1:38:58:bd:dc": {"DeviceID": 1}, "a4:c1:38:dc:d2:ee": {"DeviceID": 2}, "a4:c1:38:d6:75:f1": {"DeviceID": 3}, "a4:c1:38:90:eb:83": {"DeviceID": 4}}'))

blescan.scan(devices)

print(json.dumps(devices, indent=4, sort_keys=True, default=str))
