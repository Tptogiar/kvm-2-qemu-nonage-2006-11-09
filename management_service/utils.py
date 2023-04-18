#The following is to allow the xmlRPC to work over unix socket
from SocketServer import UnixStreamServer
from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCDispatcher, SimpleXMLRPCRequestHandler
from xmlrpclib import ServerProxy, Fault, Transport
from socket import socket, AF_UNIX, SOCK_STREAM
from httplib import HTTP, HTTPConnection
import threading
import os, sys, getopt, traceback


class launchVm(threading.Thread):
    # Override Thread's __init__ method to accept the parameters needed:
    def __init__(self, vmParams):
        self.vmParams = vmParams
        threading.Thread.__init__(self, name=self.vmParams[1])

    def run(self):
        pid = os.fork()
        if pid == 0:
            for fd in range(3, 1024):
                try:
                    flags = fcntl.fcntl(fd, fcntl.F_GETFD)
                    flags |= fcntl.FD_CLOEXEC
                    fcntl.fcntl(fd, fcntl.F_SETFD, flags)
                except:
                    pass
            os.execv(self.vmParams[0], self.vmParams)
        else:
            os.wait()




# Create communication channel to vm's wrappers to regain connection 
class UnixStreamXMLRPCServer(UnixStreamServer, SimpleXMLRPCDispatcher):
    def __init__(self, addr, requestHandler=SimpleXMLRPCRequestHandler):
        self.logRequests = 0 # critical, as logging fails with UnixStreamServer
        SimpleXMLRPCDispatcher.__init__(self)
        UnixStreamServer.__init__(self, addr, requestHandler)


class unixSocketXMLRPC(threading.Thread):
    def __init__(self, addr):
        self.server = UnixStreamXMLRPCServer(addr)
        self.server.register_introspection_functions()
        threading.Thread.__init__(self)

    def register_function(self, func, name):
        self.server.register_function(func, name)

    def run(self):
        self.stoppable_run()

    def stoppable_run(self):
        self.enabled = True
        while self.enabled:
            self.server.handle_request()

    def stop(self):
        self.enabled = False
        self.server.server_close()


class UnixStreamTransport(Transport):
    def __init__ (self, socketFile):
        self.socketFile = socketFile

    def make_connection(self, host):
        socketFile = self.socketFile
        
        class UnixStreamHTTPConnection(HTTPConnection):
            def connect(self):
                self.sock = socket(AF_UNIX, SOCK_STREAM)
                self.sock.connect(socketFile)

        class UnixStreamHTTP(HTTP):        
            _connection_class = UnixStreamHTTPConnection

        return UnixStreamHTTP(socketFile) # overridden, but prevents IndexError

