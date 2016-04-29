# Luke Garrison
# 4/28/2016
# home

from twisted.internet.protocol import Factory, Protocol, ClientFactory
from twisted.internet.tcp import Port
from twisted.internet import reactor
from twisted.internet.defer import DeferredQueue

COMMAND_CONN_PORT = 40212
DATA_CONN_PORT = 42212
SSH_PORT = 9007

class HomeClientConnection(Protocol):
    def __init__(self, addr, homeWorkCommandConnection):
        self.addr = addr
        self.homeWorkCommandConnection = homeWorkCommandConnection
        self.deferredQueue = DeferredQueue()
        print "connection received from", addr

    def startForwarding(self, homeWorkDataConnection):
        self.homeWorkDataConnection = homeWorkDataConnection
        self.deferredQueue.get().addCallback(self.sendData)
    
    def sendData(self, data):
        self.homeWorkDataConnection.transport.write(data)
        self.deferredQueue.get().addCallback(self.sendData)

    def connectionMade(self):
        self.homeWorkCommandConnection.createHomeWorkDataConnection(self)

    def dataReceived(self, data):
        self.deferredQueue.put(data)

    def connectionLost(self, reason):
        print "connection lost from ", self.addr

class HomeClientConnectionFactory(Factory):
    def __init__(self, homeWorkCommandConnection):
        self.homeWorkCommandConnection = homeWorkCommandConnection

    def buildProtocol(self, addr):
        return HomeClientConnection(addr, self.homeWorkCommandConnection)


class homeWorkCommandConnection(Protocol):
    def __init__(self, addr):
        # save addr for later use
        self.addr = addr
        print "connection received from", addr
        reactor.listenTCP(SSH_PORT, HomeClientConnectionFactory(self))

    def dataReceived(self, data):
        if data == "drop data connection":
            self.dataConnection.stopListening()
        pass

    def connectionLost(self, reason):
        print "connection lost from", self.addr

    def createHomeWorkDataConnection(self, HC):
        self.HC = HC

        # start listening for data coming from the data connection
        self.dataConnection = reactor.listenTCP(DATA_CONN_PORT, HomeWorkDataConnectionFactory(HC))

        # start data connection on work computer
        self.transport.write("start data connection")

class homeWorkCommandConnectionFactory(Factory):
    def buildProtocol(self, addr):
        return homeWorkCommandConnection(addr)


class HomeWorkDataConnection(Protocol):
    def __init__(self, addr, homeClientConnection):
        self.addr = addr
        self.homeClientConnection = homeClientConnection

    def connectionMade(self):
        self.homeClientConnection.startForwarding(self)

    def dataReceived(self, data):
        # forward data to homeClientConnection
        self.homeClientConnection.transport.write(data)

    def connectionLost(self, reason):
        print "connection lost from", self.addr

class HomeWorkDataConnectionFactory(Factory):
    def __init__(self, homeClientConnection):
        self.homeClientConnection = homeClientConnection

    def buildProtocol(self, addr):
        return HomeWorkDataConnection(addr, self.homeClientConnection)


reactor.listenTCP(COMMAND_CONN_PORT, homeWorkCommandConnectionFactory())

reactor.run()

