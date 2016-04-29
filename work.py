# Luke Garrison
# 4/28/2016
# work

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet.defer import DeferredQueue

HOME_ADDRESS = "student02.cse.nd.edu"
COMMAND_PORT = 40212
DATA_PORT = 42212

SSH_ADDRESS = "student02.cse.nd.edu"
SSH_PORT = 22 # the "service"

class HomeWorkCommandConnection(Protocol):
    def connectionMade(self):
        print "new connection made to", HOME_ADDRESS, "port", COMMAND_PORT
        
    def dataReceived(self, data):
        if data == "start data connection":
            reactor.connectTCP(HOME_ADDRESS, DATA_PORT, HomeWorkDataConnectionFactory(self))
        return

    def dropDataConnection(self):
        # home.py is listening for this command. If it receives it, it will stop listening
        # on the data port
        self.transport.write("drop data connection")

    def connectionLost(self, reason):
        print "lost connection to", HOME_ADDRESS, "port", COMMAND_PORT


class HomeWorkCommandConnectionFactory(ClientFactory):
    def buildProtocol(self, addr):
        return HomeWorkCommandConnection()



class HomeWorkDataConnection(Protocol):
    def __init__(self, homeWorkCommandConnection):
        self.homeWorkCommandConnection = homeWorkCommandConnection

    def connectionMade(self):
        print "new connection made to", HOME_ADDRESS, "port", COMMAND_PORT
        # initialize connection to service/ssh
        reactor.connectTCP(SSH_ADDRESS, SSH_PORT, WorkServiceConnectionFactory(self))
        self.deferredQueue = DeferredQueue()

    def dataReceived(self, data):
        self.deferredQueue.put(data)
        return

    def connectionLost(self, reason):
        print "lost connection to", HOME_ADDRESS, "port", COMMAND_PORT

    def dropConnection(self):
        self.homeWorkCommandConnection.dropDataConnection()

class HomeWorkDataConnectionFactory(ClientFactory):
    def __init__(self, homeWorkCommandConnection):
        self.homeWorkCommandConnection = homeWorkCommandConnection

    def buildProtocol(self, addr):
        return HomeWorkDataConnection(self.homeWorkCommandConnection)



class WorkServiceConnection(Protocol):
    def __init__(self, homeWorkDataConnection):
        self.homeWorkDataConnection = homeWorkDataConnection

    def connectionMade(self):
        print "new connection made to", HOME_ADDRESS, "port", SSH_PORT
        self.homeWorkDataConnection.deferredQueue.get().addCallback(self.sendData)

    def dataReceived(self, data):
        # send data received from ssh back to home
        self.homeWorkDataConnection.transport.write(data)
        return

    def sendData(self, data):
        # send data to ssh
        self.transport.write(data)
        self.homeWorkDataConnection.deferredQueue.get().addCallback(self.sendData)

    def connectionLost(self, reason):
        self.homeWorkDataConnection.dropConnection()

class WorkServiceConnectionFactory(ClientFactory):
    def __init__(self, homeWorkDataConnection):
        self.homeWorkDataConnection = homeWorkDataConnection

    def buildProtocol(self, addr):
        return WorkServiceConnection(self.homeWorkDataConnection)


if __name__ == "__main__":
    reactor.connectTCP(HOME_ADDRESS, COMMAND_PORT, HomeWorkCommandConnectionFactory())


    reactor.run()
