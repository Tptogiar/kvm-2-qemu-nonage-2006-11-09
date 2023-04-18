#!/usr/bin/python

import sys
import time
import os, sys, getopt, traceback
import xmlrpclib
import re


def usage(cmd):
    print "Usage:  client.py <server> [OPTIONS] <command> [Command parameters]"
    print "\nOptions"
    print "-h\tDisplay this help"
    print "\nCommands"
    for entry in cmd.keys():
        print entry  
        for line in cmd[entry][1]:
            print '\t' + line


def printConf(conf):
    print conf['vmName']
    print "\tStatus = " + conf['status']
    for element in conf.keys():
        if element not in ('vmName', 'status'):
            print "\t%s = %s" % (element, conf[element])  

class service:
    def do_connect(self, server, port):
        self.s = xmlrpclib.Server('http://' + server + ':' + port)

    def ExecAndExit(func, response):
        if response[0] != 0:
            print response[1]
        else:
            printConf(response[1])
        sys.exit(response[0])


    def do_test(self, args):
        print self.s.class_test(args)

    def do_create(self, args):
        params={'cdrom': '', 'boot': '', 'snapshotFile': '', 'vt': False}
        confFile = open(args[0])
        for line in confFile.readlines():
            line = re.sub("\s+", '', line)
            line = re.sub("\#.*", '', line)
            if '=' in line:
                param,value = line.split("=")
                params[param] = value
        if len(args) > 1:
            for line in args[1:]:
                param,value = line.split("=")
                params[param] = value
        if params['vt'] is not False:
            params['vt'] = bool(params['vt'] in ('True'))
        self.ExecAndExit(self.s.create(params['vmName'], params['memSize'], params['imageFile'], params['display'], 
                            params['cdrom'], params['boot'], params['snapshotFile'], params['vt'] ))

    def do_changeCdFile(self, args):
        vmName = args[0]
        file = args[1]
        self.ExecAndExit(self.s.changeCdFile(vmName, file))

    def do_list(self):
        status, list = self.s.list()
        for conf in list:
            printConf(conf)
        sys.exit(status)

    def do_destroy(self, args):
        vmName = args[0]
        status , message = self.s.destroy(vmName)
        print message
        sys.exit(status)

    def do_pause(self, args):
        vmName = args[0]
        self.ExecAndExit(self.s.pause(vmName))

    def do_continue(self, args):
        vmName = args[0]
        self.ExecAndExit(self.s.cont(vmName))

    def do_shutdown(self, args):
        vmName = args[0]
        self.ExecAndExit(self.s.shutdown(vmName))

    def do_reset(self, args):
        vmName = args[0]
        self.ExecAndExit(self.s.reset(vmName))

    def do_snapshot(self, args):
        vmName = args[0]
        file = args[1]
        self.ExecAndExit(self.s.snapshot(vmName, file))


if __name__ == '__main__':
    try:
        serverPort = "54321"
        printHelp = False
        serv = service()
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
        commands = {
            'class_test' : (serv.do_test, ('  ', '  ')),
            'create'  :  ( serv.do_create,
                           ('<configFile> [parameters]',
                            'Creates new machine with the paremeters givven in the command line overriding the ones in the config file',
                            'Example with config file: mclient.py someServer create myVmConfigFile',
                            'Example with no file    : mclient.py someServer create /dev/null vmName=someName memSize=256 imageFile=someImage display=<vnc|local>' 
                            )),
            'changeCD':  ( serv.do_changeCdFile,
                           ('<vmName> <fileName>', 
                            'Changes the iso image of the cdrom'
                           )),
            'destroy' :  ( serv.do_destroy,
                           ('<vmName>',
                            'Stops the emulation and destroys the virtual machine. This is not a shutdown.'
                           )),
            'list'    :  ( serv.do_list, 
                           ('Lists all available machines on the specified server',''
                           )),
            'pause'   :  ( serv.do_pause,
                           ('<vmName>',
                            'Pauses the execution of the virtual machine without termination'
                           )),
            'continue':  ( serv.do_continue,
                           ('<vmName>',
                            'Continues execution after of a paused machine'
                           )),
            'reset'   :  ( serv.do_reset,
                           ('<vmName>',
                            'Sends reset signal to the vm'
                           )),
            'shutdown':  ( serv.do_shutdown,
                           ('<vmName>',
                            'Sends shutdown signal to the vm'
                           )),
            'snapshot':  ( serv.do_snapshot,
                           ('<vmName> <fileName>', 
                            'save the whole virtual machine state to fileName'
                           ))
        }
        for o,v in opts:
            o = o.lower()
            if o == "-h" or o == "--help":
                usage(commands)
                sys.exit(0)
        if len(args) < 2:
            raise Exception("Need at least two arguments")
        server, command = args[0:2]
        if command not in commands:
            raise Exception("Unknown command")

    except Exception, e:
        print "ERROR - %s"%(e)
        usage(commands)
        sys.exit(-1)


    try:
        serv.do_connect(server, serverPort)
        if command in ('list'):
            commands[command][0]()
        else:
            commandArgs = args[2:]
            commands[command][0](commandArgs)
    except (TypeError, IndexError):
       print "Error using command\n"
       print command
       for line in commands[command][1]:
           print '\t' + line
       
       traceback.print_exc()
       sys.exit(-1)
    except SystemExit, status:
        sys.exit(status)
    except:
        traceback.print_exc()
        sys.exit(-1)
