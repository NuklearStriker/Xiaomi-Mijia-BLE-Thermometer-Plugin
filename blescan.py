#!/usr/bin/env python3
from __future__ import print_function

import Domoticz
import json
import datetime
from bluepy import btle
import urllib.request
import base64

class ScanProcess(btle.DefaultDelegate):
    
    def __init__(self, _devices, _sensitivity=-128):
        btle.DefaultDelegate.__init__(self)
        self.devices = _devices
        self.sensitivity = _sensitivity

    def handleDiscovery(self, dev, isNewDev, isNewData):
        Name = ""
        
        if isNewDev:
            status = "new"
        elif isNewData:
            status = "update"
        else:
            status = "old"
        
        _conn = '' if dev.connectable else '(not connectable)'
        Domoticz.Debug('(handleDiscovery) Device ('+status+'): '+dev.addr+' ('+dev.addrType+'), '+str(dev.rssi)+' dBm '+_conn+'')
                
        if dev.rssi < self.sensitivity:
            return
                
        for (sdid, desc, val) in dev.getScanData():
            if sdid in [8, 9]:
                Name = val
            elif sdid == 22:
                Payload = val

        if (Name[:4] == "ATC_") and (dev.addr in self.devices):
                comfort = 0
                
                _device = self.devices[dev.addr]

                _device.update({'Name': Name})
                _device.update({'Temperature' : int(Payload[16:20], 16)/10})
                _device.update({'Humidity' : int(Payload[20:22], 16)})
                
                if float(_device['Humidity']) < 40:
                    comfort = 2
                elif float(_device['Humidity']) <= 70:
                    comfort = 1
                elif float(_device['Humidity']) > 70:
                    comfort = 3
                        
                _device.update({'Comfort' : comfort})
                _device.update({'Battery' : int(Payload[22:24], 16)})
                _device.update({'sensitivity' : dev.rssi})
                _device.update({'lastCollect' : str(datetime.datetime.now())})
                
                Domoticz.Debug('(handleDiscovery) '+json.dumps(_device,default=str))
        else:
            return

def scan(devices, hci=0, timeout=5, sensitivity=-128):
    
    Domoticz.Debug("(scan) hci = hci"+str(hci))
    Domoticz.Debug("(scan) timeout = "+str(timeout)+"sec")
    Domoticz.Debug("(scan) sensitivity = "+str(sensitivity)+"dBm")
    
    btle.Debugging = False
    scanner = btle.Scanner(hci).withDelegate(ScanProcess(devices,sensitivity))
    scanner.scan(timeout)
    
    return