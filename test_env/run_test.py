#!/usr/bin/python

import sys
import time
import os, sys, getopt, traceback
import xmlrpclib
import re
import ConfigParser


def usage():
    print "Usage:  run_test.py [options] test_file"
    print "\nOptions"
    print "-h\tDisplay this help"



def parse_config_file(testFile):

    try:
        hostFilePointer = os.stat(testFile)
    except OSError, (errno, strerror):
        print "I/O error(%s): %s - error opening config file \"%s\"\n\n" % (errno, strerror, testFile)
        raise

    try:
        cp = ConfigParser.ConfigParser()
        cp.read([testFile])
        return cp
    except:
        print('Could not parse configuration file %s' % (testFile))
        traceback.print_exc()
        return None



def run(testFile):
    print "Test file is: " + testFile
    cp = parse_config_file(testFile)
    commands = cp.items('commands')


    machines = {}
    machineIndex = 0

    try:
        while 1:
            machineIndex += 1
            machine = 'machine' + str(machineIndex)
            machines[machine] = {}
            for var, val in cp.items(machine):
                machines[machine][var] = val 
    except:
        del machines[machine]
        pass

    print machines



if __name__ == '__main__':
    try:
        printHelp = False
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
        for o,v in opts:
            o = o.lower()
            if o == "-h" or o == "--help":
                usage()
                sys.exit(0)
        if len(args) < 1:
            raise Exception("Test file needed")
        testFile = args[0]
    except Exception, e:
        print "ERROR - %s"%(e)
        usage()
        sys.exit(-1)


    try:
        run(testFile)
    except SystemExit, status:
        sys.exit(status)
    except:
        traceback.print_exc()
        sys.exit(-1)
