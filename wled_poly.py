#!/usr/bin/env python3

"""
This is a NodeServer for WLED written by automationgeek (Jean-Francois Tremblay) 
based on the NodeServer template for Polyglot v2 written in Python2/3 by Einstein.42 (James Milne) milne.james@gmail.com.
Using this Python Library to control WLED by https://github.com/pctechjon/wledpy
"""

import polyinterface
import time
import json
import sys
import os
import zipfile
import wledpy.wled as wled
from threading import Thread

LOGGER = polyinterface.LOGGER

with open('server.json') as data:
    SERVERDATA = json.load(data)
try:
    VERSION = SERVERDATA['credits'][0]['version']
except (KeyError, ValueError):
    LOGGER.info('Version not found in server.json.')
    VERSION = '0.0.0'

class Controller(polyinterface.Controller):

    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'WLED'
        self.initialized = False
        self.tries = 0
        self.myHost = None
        self.discovery_thread = None
        self.hb = 0
        
    def start(self):
        LOGGER.info('Started NanoLeaf WLED for v2 NodeServer version %s', str(VERSION))
        try:
            
            # Get and set IP
            if 'host' in self.polyConfig['customParams'] :
                self.myHost = self.polyConfig['customParams']['host']
                LOGGER.info('Custom IP address specified: {}'.format(self.host))
            else:
                LOGGER.error('Need to have ip address in custom param host')
                self.setDriver('ST', 0, True)
                return False                
                        
            self.setDriver('ST', 1, True)
            self.discover()
                                                            
        except Exception as ex:
            LOGGER.error('Error starting WLED NodeServer: %s', str(ex))
            self.setDriver('ST', 0)
            return False

    def shortPoll(self):
        self.query()

    def longPoll(self):
        self.heartbeat()
        if self.discovery_thread is not None:
            if self.discovery_thread.is_alive():
                LOGGER.debug('Skipping longPoll() while discovery in progress...')
                return
            else:
                self.discovery_thread = None
                self.query()

    def heartbeat(self):
        LOGGER.debug('heartbeat: hb={}'.format(self.hb))
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0

    def query(self):
        self.setDriver('ST', 1, True)
        for node in self.nodes:
            if self.nodes[node].address != self.address and self.nodes[node].do_poll:
                self.nodes[node].query()
        self.reportDrivers()
    def install_profile(self):
        try:
            self.poly.installprofile()
            LOGGER.info('Please restart the Admin Console for change to take effect')
        except Exception as ex:
            LOGGER.error('Error installing profile: %s', str(ex))
        return True
   
    def runDiscover(self,command):
        self.discover()
    
    def discover(self, *args, **kwargs):  
        if self.discovery_thread is not None:
            if self.discovery_thread.is_alive():
                LOGGER.info('Discovery is still in progress')
                return
        self.discovery_thread = Thread(target=self._discovery_process)
        self.discovery_thread.start()

    def _discovery_process(self):
        lstIp = self.myHost.split(',')
        id = 1
        for ip in lstIp:
            self.addNode(WledNode(self, self.address, 'wled' + str(id) , 'wled' + str(id), ip))
            id = id + 1 

    def delete(self):
        LOGGER.info('Deleting WLED')
        
    id = 'controller'
    commands = {'DISCOVERY' : runDiscover}
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 2}]
    
class WledNode(polyinterface.Node):

    def __init__(self, controller, primary, address, name, ip):
        super(WledNode, self).__init__(controller, primary, address, name)
        self.do_poll = True
        self.wled_ip = ip
        self.arrEffects = None
        
        try:
            self.my_wled = wled.Wled(ip)
        except Exception as ex:
            LOGGER.error('Error unable to connect to WLED: %s', str(ex))
            
        self.__getEffetsList()
        self.__BuildProfile()
        self.query()

    def start(self):
        pass
        
    def setOn(self, command):
        self.my_wled.turn_on()
        self.setDriver('ST', 100, True)

    def setOff(self, command):
        self.my_wled.turn_off()
        self.setDriver('ST', 0, True)
        
    def setBrightness(self, command):
        intBri = int(command.get('value'))
        self.my_wled.set_brightness(intBri)                                            
        self.setDriver('GV3', intBri, True)

    def setEffect(self, command):
        self.my_wled.set_effect(int(command.get('value')))
        self.setDriver('GV4', intEffect, True)
    
    def setProfile(self, command):
        self.__saveEffetsList()
        self.__BuildProfile()
    
    def query(self):
        self.__updateValue()

    def __updateValue(self):
        try:
            if self.my_wled.is_on() :
                self.setDriver('ST', 100, True)
            else:
                self.setDriver('ST', 0, True)
            self.setDriver('GV3', self.my_wled.get_brightness(), True)
            self.setDriver('GV4', self.arrEffects.index(self.my_wled.get_effect())+1, True)
            self.reportDrivers()
        except Exception as ex:
            LOGGER.error('Error updating WLED value: %s', str(ex))
    
    def __saveEffetsList(self):
        try:
            self.arrEffects = self.my_wled.get_effects()
        except Exception as ex:
            LOGGER.error('Unable to get WLED Effet List: %s', str(ex))
            
        #Write effectLists to Json
        try:
            with open(".effectLists.json", "w+") as outfile:
                json.dump(self.arrEffects, outfile)
        except IOError:
            LOGGER.error('Unable to write effectLists.json')
              
    def __getEffetsList(self):
        try:
            with open(".effectLists.json", "r") as infile:
                self.arrEffects = json.load(infile)
        except IOError:
            self.__saveEffetsList()
    
    def __BuildProfile(self):
        try:
            # Build File NLS from Template
            with open("profile/nls/en_us.template") as f:
                with open("profile/nls/en_us.txt", "w+") as f1:
                    for line in f:
                        f1.write(line) 
                    f1.write("\n") 
                f1.close()
            f.close()

            # Add Effect to NLS Profile        
            with open("profile/nls/en_us.txt", "a") as myfile:
                intCounter = 1
                for x in self.arrEffects:  
                    myfile.write("EFFECT_SEL-" + str(intCounter) + " = " + x + "\n")
                    intCounter = intCounter + 1
            myfile.close()

            intArrSize = len(self.arrEffects)
            if intArrSize is None or intArrSize == 0 :
                intArrSize = 1

            with open("profile/editor/editors.template") as f:
                with open("profile/editor/editors.xml", "w+") as f1:
                    for line in f:
                        f1.write(line) 
                    f1.write("\n") 
                f1.close()
            f.close()

            with open("profile/editor/editors.xml", "a") as myfile:
                myfile.write("\t<editor id=\"MEFFECT\">"  + "\n")
                myfile.write("\t\t<range uom=\"25\" subset=\"1-"+ str(intArrSize) + "\" nls=\"EFFECT_SEL\" />"  + "\n")
                myfile.write("\t</editor>" + "\n")
                myfile.write("</editors>")
            myfile.close()
        
        except Exception as ex:
            LOGGER.error('Error generating profile: %s', str(ex))
        
        self.parent.install_profile()

        
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 78},
               {'driver': 'GV3', 'value': 0, 'uom': 51},
               {'driver': 'GV4', 'value': 1, 'uom': 25}]
    
    id = 'WLED'
    commands = {
                    'QUERY': query,            
                    'DON': setOn,
                    'DOF': setOff,
                    'SET_PROFILE' : setProfile,
                    'SET_BRI': setBrightness,
                    'SET_EFFECT': setEffect
                }
    
if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('WledNodeServer')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
