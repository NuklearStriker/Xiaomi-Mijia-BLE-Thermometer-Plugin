#           Xiaomi Mijia BLE Thermometer Plugin
#
#           Author:     LECLERCQ Kevin, 2021
#
"""
<plugin key="Xiaomi-Mijia-BLE-Thermometer" name="Xiaomi Mijia BLE Thermometer Plugin" author="LECLERCQ Kevin" version="1.0.0" externallink="https://github.com/NuklearStriker/Xiaomi-Mijia-BLE-Thermometer-Plugin">
    <description>
        Xiaomi Mijia BLE Thermometer Plugin.<br/><br/>
        Prerequisites:<br/>
        You need to flash your device following&nbsp;<a href="https://github.com/atc1441/ATC_MiThermometer">this link</a>.
    </description>
    <params>
        <param field="Address" label="Mac address(es) comma separated" width="300px" required="true"/>
        <param field="Mode1" label="Refresh rate" width="40px">
            <options>
                <option label="10" value="10" default="true" />
                <option label="15" value="15"/>
                <option label="20" value="20"/>
                <option label="25" value="25"/>
                <option label="30" value="30"/>
                <option label="45" value="45"/>
                <option label="60" value="60"/>
            </options>
        </param>
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Python" value="18"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
import blescan
from datetime import date, datetime, timedelta
import json
import os

    
class BasePlugin:
    macList = []
    dicoAll = {}
    _fileNameDeviceMapping = "devices.json"
    
    def loadDicoAllDevice(self):
        if not self.dicoAll:
            if (os.path.isfile(Parameters["HomeFolder"]+self._fileNameDeviceMapping)):
                with open(Parameters["HomeFolder"]+self._fileNameDeviceMapping) as data_file:
                    self.dicoAll = json.load(data_file)
            Domoticz.Debug("Dico loaded...")

    def saveDicoDevice(self):
        with open(Parameters["HomeFolder"]+self._fileNameDeviceMapping, 'w', encoding='utf-8') as data_file:
                json.dump(self.dicoAll, data_file)
        Domoticz.Debug("Dico saved...")
        
    def cleanDicoDevice(self):
        for mac in self.dicoAll:
            if mac not in self.macList:
                Domotiz.Debug('Warning: "'+mac+'" is still in the Dico but not in the configuration.')
                Unit = self.dicoAll[mac]["DeviceID"]
                if Unit in Devices:
                    Devices[Unit].Delete()

    def getOrCreateIdForDevice(self, mac):
        if(mac in self.dicoAll):
            DeviceID = self.dicoAll[mac]["DeviceID"]
            Domoticz.Debug("Device found - ID : "+str(DeviceID))
        else:
            Domoticz.Debug("Device not found, Create One...")
            DeviceID = len(Devices)+1
            self.dicoAll.update({mac:{"DeviceID":DeviceID}})
            Domoticz.Debug("Device created, ID : "+str(DeviceID))
            self.saveDicoDevice()
        return DeviceID
    
    def onStart(self):
        if Parameters["Mode6"] != "0":
            DumpConfigToLog()
            Domoticz.Debugging(int(Parameters["Mode6"]))
        
        self.loadDicoAllDevice()
        
        Domoticz.Debug("Refresh rate : "+str(Parameters["Mode1"]))
        Domoticz.Heartbeat(int(Parameters["Mode1"]))
        
        # Split the list of address
        self.macList = Parameters["Address"].replace(" ", "").split(",")
        
        # Find if device already exist
        for destination in self.macList:
            Domoticz.Debug("Searching for '"+destination+"'...")
            keyunit = self.getOrCreateIdForDevice(destination)
            if (keyunit not in Devices):
                Domoticz.Device(Name=destination, Unit=keyunit, Type=82, Subtype=1).Create()
                Domoticz.Debug("Created device: "+Devices[keyunit].Name+"("+str(keyunit)+")")

    def onStop(self):
        Domoticz.Debug("onStop called")
        self.saveDicoDevice()
 
    def onConnect(self, Connection, Status, Description):
        if (Status == 0):
            Domoticz.Debug("Successful connect to: "+Connection.Address+" which is surprising because BLE<BEACON> is connectionless.")
        else:
            Domoticz.Debug("Failed to connect to: "+Connection.Address+", Description: "+Description)

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called for connection: '"+Connection.Name+"'")

    def onHeartbeat(self):
        Domoticz.Debug("Heartbeating...")
        _timeout = 5 if int(Parameters["Mode1"]) == 10 else 10
        blescan.scan(devices=self.dicoAll,timeout=_timeout)
        for mac in self.dicoAll:
            device = self.dicoAll[mac]
            if ( datetime.now() - timedelta(seconds=int(Parameters["Mode1"]))) < datetime.fromisoformat(device["lastCollect"]):
                _nValue = 0
                _sValue = str(device["Temperature"])+';'+str(device["Humidity"])+';'+str(device["Comfort"])
                _batteryLevel = device["Battery"]
                UpdateDevice(device["DeviceID"],_nValue,_sValue,_batteryLevel)

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()
    
def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

def UpdateDevice(Unit, nValue, sValue, BatteryLevel):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or (Devices[Unit].BatteryLevel != BatteryLevel):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), BatteryLevel=BatteryLevel)
            Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+") : Batt :"+str(BatteryLevel))
    return

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Log( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Log("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Log("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Log("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Log("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Log("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Log("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Log("Device LastLevel: " + str(Devices[x].LastLevel))
    return