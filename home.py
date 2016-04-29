# Luke Garrison
# 4/28/2016
# home

from twisted.internet.protocol import Factory, Protocol, ClientFactory
from twisted.internet.tcp import Port
from twisted.internet import reactor
from twisted.internet.defer import DeferredQueue

# queue = DeferredQueue()
# queue2 = DeferredQueue()

COMMAND_CONN_PORT = 32001
DATA_CONN_PORT = 32002
SSH_PORT = 9007

SERVER_HOST = "student02.cse.nd.edu"
SERVER_PORT = 40001


class HomeClientConnection(Protocol):
    def __init__(self, addr, homeWorkConnection):
        self.addr = addr
        self.homeWorkConnection = homeWorkConnection
        self.deferredQueue = DeferredQueue()
        print "connection received from", addr

    def startForwarding(self, homeWorkDataConnection):
        print "start forwarding"
        self.homeWorkDataConnection = homeWorkDataConnection
        self.deferredQueue.get().addCallback(self.sendData)
    
    def sendData(self, data):
        print "sendData called"
        self.homeWorkDataConnection.transport.write(data)
        self.deferredQueue.get().addCallback(self.sendData)

    def connectionMade(self):
        self.homeWorkConnection.createHomeWorkDataConnection(self)

    def dataReceived(self, data):
        self.deferredQueue.put(data)
        print "data received here"
        print data

    def connectionLost(self, reason):
        print "connection lost from ", self.addr

class HomeClientConnectionFactory(Factory):
    def __init__(self, homeWorkConnection):
        self.homeWorkConnection = homeWorkConnection

    def buildProtocol(self, addr):
        return HomeClientConnection(addr, self.homeWorkConnection)


class HomeWorkConnection(Protocol):
    def __init__(self, addr):
        # save addr for later use
        self.addr = addr
        print "connection received from", addr
        # reactor.connectTCP(SERVER_HOST, SERVER_PORT, ProxyClientFactory());
        reactor.listenTCP(SSH_PORT, HomeClientConnectionFactory(self))

    def dataReceived(self, data):
        # queue2.put(data)
        # queue.get().addCallback(self.sendResponseToClient)
        print data

    def connectionLost(self, reason):
        print "connection lost from", self.addr
        # reactor.stop()

    def createHomeWorkDataConnection(self, HC):
        self.HC = HC

        # start listening for data coming from the data connection
        reactor.listenTCP(DATA_CONN_PORT, HomeWorkDataConnectionFactory(HC))

        # start data connection on work computer
        self.transport.write("start data connection")

class HomeWorkConnectionFactory(Factory):
    def buildProtocol(self, addr):
        return HomeWorkConnection(addr)


class HomeWorkDataConnection(Protocol):
    def __init__(self, addr, homeClientConnection):
        print "listening for data connection"
        self.addr = addr
        self.homeClientConnection = homeClientConnection

    def connectionMade(self):
        self.homeClientConnection.startForwarding(self)

    def dataReceived(self, data):
        # forward data to homeClientConnection
        self.homeClientConnection.transport.write(data)
        print "here 4"

    def connectionLost(self, reason):
        print "connection lost from", self.addr

class HomeWorkDataConnectionFactory(Factory):
    def __init__(self, homeClientConnection):
        self.homeClientConnection = homeClientConnection

    def buildProtocol(self, addr):
        return HomeWorkDataConnection(addr, self.homeClientConnection)


reactor.listenTCP(COMMAND_CONN_PORT, HomeWorkConnectionFactory())

reactor.run()

