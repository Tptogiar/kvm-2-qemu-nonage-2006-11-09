#!/usr/bin/python

import os, sys, getopt, traceback
import time
import threading

#The following is to allow the xmlRPC to work over unix socket
from utils import *
from define import * 
from xmlrpclib import ServerProxy, Fault, Transport

class vm:
    def __init__(self, vmName, memSize, imageFile, display, cdrom, boot , snapshotFile, socketFile, executable):
       self.conf = {}
       self.conf['vmName'] = vmName
       self.conf['display'] = int(display)
       self.conf['memSize'] = memSize 
       self.conf['diskImage'] = imageFile
       self.conf['cdrom'] = cdrom
       self.conf['boot'] = boot
       self.conf['snapshotFile'] = snapshotFile
       self.socketFile = '/tmp/' + self.conf['vmName'] + '.socket'
       self.serverSocket = socketFile
       self.executable = executable
       self.enable = True

    def run(self):
        if (self.conf['display'] != 0):
            display = " -vnc %d " % (self.conf['display'])
        else:
            display = ""
        if self.conf['boot'] is not '':
            boot = ' -boot ' + self.conf['boot'] + ' '
        else:
            boot = ''
        if self.conf['cdrom'] is not '':
            cdrom = ' -cdrom ' + self.conf['cdrom'] + ' '
        else:
            cdrom = ''
        if self.conf['snapshotFile'] is not '':
            snapshot = ' -loadvm ' + self.conf['snapshotFile'] + ' '
        else:
            snapshot = ''

        print "VM - %s has started with image %s\n" % (self.conf['vmName'], self.conf['diskImage'])
        runCommand = (self.executable + " -monitor stdio -m " + 
                      self.conf['memSize'] + " " + self.conf['diskImage'] + display +
                      cdrom + boot + snapshot)
        print runCommand + "\n"
        self.cmdStdin, self.cmdStdout, self.cmdStderr = os.popen3(runCommand)
        self.connectToServer()
        self.setUpVmServer()
        self.maintain()

    def connectToServer(self):
        self.proxy = ServerProxy('http://' + self.serverSocket, transport=UnixStreamTransport(self.serverSocket))
        self.proxy.register(self.conf['vmName'], self.socketFile)

    def setUpVmServer(self):
        try:
            os.unlink(self.socketFile)
        except os.error:
            pass
        self.localServer = unixSocketXMLRPC(self.socketFile)

        self.localServer.register_function(self.doCommand, 'doCommand')
        self.localServer.register_function(self.status, 'status')
        self.localServer.register_function(self.destroy, 'destroy')
        self.localServer.register_function(self.getLastStatus, 'getLastStatus')
        self.localServer.start()

    def doCommand(self, command):
        self.status()
        if self.lastStatus != 'Down':
            self.cmdStdin.write(command + "\n")
            self.cmdStdin.flush()
            return (0, self.status())
        else:
            return errCode['down'] 

    def destroy(self):
        self.status()
        if self.lastStatus != 'Down':
            self.cmdStdin.write("quit \n")
            self.cmdStdin.flush()
        self.localServer.stop()
        self.enable = False
        return (0,'Done')

    def getLastStatus(self):
        return self.lastStatus

    def maintain(self):
        alive = True
        while self.enable: 
            try:
                self.proxy.isAlive()
                if not alive:
                    print "register VM"
                    self.proxy.register(self.conf['vmName'], self.socketFile)
                alive = True
            except:
                print "Server is dead"
                alive = False
            time.sleep(1)

    def status(self):
        vmStatus = ''
        try:
             self.cmdStdin.write("help\n")
             self.cmdStdin.flush()
             self.lastStatus = 'Up'
             vmStatus = "    Machine status: Up\n"
        except:
             self.lastStatus = 'Down'
             vmStatus = "    Machine status: Down\n"
#        for element in self.conf.keys():
#            if element in ('display'):
#                vmStatus = vmStatus + "    " + element + ": " + str(self.conf[element]) + "\n"  
#            else:
#                vmStatus = vmStatus + "    " + element + ": " + self.conf[element] + "\n"  
#        return vmStatus 
        self.conf['status'] = self.lastStatus
        return self.conf 



if __name__ == '__main__':

    args = sys.argv[1:]
    try: 
        print "VM has started"
        vmName, memSize, imageFile, display, cdrom, boot, snapshotFile, socketFile, executable = args 
        vmInstance = vm(vmName, memSize, imageFile, display, cdrom, boot, snapshotFile, socketFile, executable)
        vmInstance.run()
    except:
        traceback.print_exc()
        sys.exit(-1)
