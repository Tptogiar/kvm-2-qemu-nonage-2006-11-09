#!/usr/bin/python

from vm import *
from SimpleXMLRPCServer import SimpleXMLRPCServer
import os, sys, getopt, traceback
import re
import time
import ConfigParser
from utils import *
from define import * 
import fcntl


def parse_config_file(confFile):
    try:
        cp = ConfigParser.ConfigParser()
        cp.read([confFile])
        return cp
    except:
        timed_print('Could not parse configuration file %s' % (hostsFile))
        return None


def usage():
    print "Usage:  mserver.py [OPTIONS]"
    print "     -h  - Display this help"
    print "     -q  - do not display output (quiet mode)"



#Get configuration
def run(vmConfFile, quiet):
    try:
        hostFilePointer = os.stat(vmConfFile)
    except OSError, (errno, strerror):
        print "I/O error(%s): %s - error opening config file \"%s\"" % (errno, strerror, vmConfFile)
        raise Exception("Unexpected arguments")
    
    cp = parse_config_file(vmConfFile)
    vars = cp.items('vars')
    varDictionary = {}
    for var, value in vars:
        varDictionary[var] = value

    addresses = cp.items('addresses')
    addressDict = {'host': ''}
    for var, value in addresses:
        addressDict[var] = value

    #Set up RPCXML server for VM wrapper objects connection
    try:
        os.unlink(addressDict['socket_file'])
    except os.error:
        pass
    localServer = unixSocketXMLRPC(addressDict['socket_file'])
    
    def register(vmName, socketFile):
        #This sets up a client instance for comunication with the registered VM
        vmContainer[vmName] = ServerProxy('http://' + socketFile, transport=UnixStreamTransport(socketFile))
        return 'Done'

    def isAlive():
        return True

    localServer.register_function(register, 'register')
    localServer.register_function(isAlive, 'isAlive')
    localServer.start()
    

    #Preparations
    vmContainer = {}

    # Create remote server
    server = SimpleXMLRPCServer((addressDict['host'], int(addressDict['port'])))
    server.register_introspection_functions()

    #add write method that also checks for existance
    def runCommand(vmName, command):
        if vmName in vmContainer:
            try:
                return vmContainer[vmName].doCommand(command)
            except:
                return errCode['conLost']
        else:
            return errCode['noVM']

    def sysDown(vmName):
        return runCommand(vmName, 'system_powerdown') 

    def sysReset(vmName):
        return runCommand(vmName, 'system_reset') 

    def destroy(vmName):
        if vmName in vmContainer:
            try:
                vmContainer[vmName].destroy()
                vmContainer[vmName].status() #another dummy request to force server to leave the accept state and actually terminate
                return errCode['noDes']
            except:
                del vmContainer[vmName]
                return (0, 'Machine destroyed')
        else:
            return errCode['noVM']

    def pause(vmName):
        return runCommand(vmName, 'stop') 

    def cont(vmName):
        return runCommand(vmName, 'cont')

    def changeCdFile(vmName, file):
        #need to check first that image exists
        status , message = runCommand(vmName, 'eject -f cdrom ')
        time.sleep(1)
        if status != 0:
            return (status, message)
        else:
            vmContainer[vmName].conf['cdrom'] = file
            return runCommand(vmName, 'change cdrom ' + file) 


    def saveState(vmName, file):
            return runCommand(vmName, 'savevm ' + file)

    def create(vmName, memSize, imageFile, display, cdrom, boot, snapshotFile, vt):
        #need to check first that images exist
        if vmContainer.has_key(vmName):
            return errCode['exist']
        if display == 'vnc':
            disId = 10
            keepSearch = True  
            while keepSearch:
                keepSearch = False  
                for entry in vmContainer:
                    if (entry == vmName) and (vmContainer[entry].conf['display'] != 0):
                        disId = vmContainer[entry].conf['display']
                        break
                    if disId == vmContainer[entry].conf['display']:
                        disId = disId + 1
                        keepSearch = True
                        break
            display = disId 
        else:
            display = 0
        if vt is True:
            executable = varDictionary['vtexec']
        else:
            executable = varDictionary['exec']

        vmParams = ('./vm.py', vmName, memSize, imageFile, str(display), cdrom, boot, snapshotFile, addressDict['socket_file'], executable)
        newVm = launchVm(vmParams)
        newVm.start()
        del newVm
        time.sleep(1)
        return (0, vmContainer[vmName].status()) 

    def list():
        list = []
        for vmName in vmContainer.keys():
            try: 
                list.append(vmContainer[vmName].status())
            except:
                list = '$s\n\tLost connection to VM, please run destroy\n' % (vmName)
        return (0, list)

    def class_test (a):
        myClass = {'vm_no1' : {'a': 1, 'b': 2}, 'vm_no2' : {'c': 3, 'd': 4}}
        return myClass

    # Register a functions can be under a different name - func,name
    server.register_function(destroy, 'destroy')
    server.register_function(create, 'create')
    server.register_function(list, 'list')
    server.register_function(pause, 'pause')
    server.register_function(cont, 'cont')
    server.register_function(sysReset, 'reset')
    server.register_function(sysDown, 'shutdown')
    server.register_function(changeCdFile, 'changeCdFile')
    server.register_function(saveState, 'snapshot')
    server.register_function(class_test, 'class_test')
    
    
    # Run the server's main loop
    server.serve_forever()




if __name__ == '__main__':
    try:
        vmConfFile = './vm.conf'
        quiet = False
        printHelp = False
        opts, args = getopt.getopt(sys.argv[1:], "ho", ["help","quiet"])
        for o,v in opts:
            o = o.lower()
            if o == "-h" or o == "--help":
                printHelp = True
            if o == "-q" or o == "--quiet":
                quiet = True
        if len(args) >= 1:
            raise Exception("Unexpected arguments")
    except Exception, e:
        print "ERROR - %s"%(e)
        usage()
        sys.exit(-1)
    if printHelp:
        usage()
        sys.exit(0)

    try:
        run(vmConfFile, quiet)
    except Exception, e:
        print e
        pass
    except:
        traceback.print_exc()
        sys.exit(-1)




