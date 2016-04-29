# Luke Garrison
# 4/28/2016
# work

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet.defer import DeferredQueue

HOME_ADDRESS = "student02.cse.nd.edu"
COMMAND_PORT = 32001
DATA_PORT = 32002
SSH_PORT = 22 # the "service"

class HomeWorkCommandConnection(Protocol):
    def connectionMade(self):
        print "new connection made to", HOME_ADDRESS, "port", COMMAND_PORT
        
    def dataReceived(self, data):
        print "received data", data
        if data == "start data connection":
            print "starting data connection"
            reactor.connectTCP(HOME_ADDRESS, DATA_PORT, HomeWorkDataConnectionFactory())
        return

    def connectionLost(self, reason):
        print "lost connection to", HOME_ADDRESS, "port", COMMAND_PORT
        # reactor.stop()


class HomeWorkCommandConnectionFactory(ClientFactory):
    def buildProtocol(self, addr):
        return HomeWorkCommandConnection()



class HomeWorkDataConnection(Protocol):
    def connectionMade(self):
        print "new connection made to", HOME_ADDRESS, "port", COMMAND_PORT
        # initialize connection to service/ssh
        reactor.connectTCP(HOME_ADDRESS, SSH_PORT, WorkServiceConnectionFactory(self))
        self.deferredQueue = DeferredQueue()

    def dataReceived(self, data):
        print "received data", data
        self.deferredQueue.put(data)
        return

    def connectionLost(self, reason):
        print "lost connection to", HOME_ADDRESS, "port", COMMAND_PORT
        # reactor.stop()

class HomeWorkDataConnectionFactory(ClientFactory):
    def buildProtocol(self, addr):
        return HomeWorkDataConnection()



class WorkServiceConnection(Protocol):
    def __init__(self, homeWorkDataConnection):
        self.homeWorkDataConnection = homeWorkDataConnection

    def connectionMade(self):
        print "new connection made to", HOME_ADDRESS, "port", SSH_PORT
        self.homeWorkDataConnection.deferredQueue.get().addCallback(self.sendData)

    def dataReceived(self, data):
        # print "received data", data
        # send data received from ssh back to home
        print "data received from ssh"
        print data
        self.homeWorkDataConnection.transport.write(data)
        return

    def sendData(self, data):
        # send data to ssh
        self.transport.write(data)
        self.homeWorkDataConnection.deferredQueue.get().addCallback(self.sendData)

    def connectionLost(self, reason):
        print "lost connection to", HOME_ADDRESS, "port", SSH_PORT
        # reactor.stop()

class WorkServiceConnectionFactory(ClientFactory):
    def __init__(self, homeWorkDataConnection):
        self.homeWorkDataConnection = homeWorkDataConnection

    def buildProtocol(self, addr):
        return WorkServiceConnection(self.homeWorkDataConnection)


if __name__ == "__main__":
    reactor.connectTCP(HOME_ADDRESS, COMMAND_PORT, HomeWorkCommandConnectionFactory())


    reactor.run()
