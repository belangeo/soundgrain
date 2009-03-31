"""     simpleOSC 0.2
    ixi software - July, 2006
    www.ixi-software.net

    simple API  for the Open SoundControl for Python (by Daniel Holth, Clinton
    McChesney --> pyKit.tar.gz file at http://wiretap.stetson.edu)
    Documentation at http://wiretap.stetson.edu/docs/pyKit/

    The main aim of this implementation is to provide with a simple way to deal
    with the OSC implementation that makes life easier to those who don't have
    understanding of sockets or programming. This would not be on your screen without the help
    of Daniel Holth.

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

    Thanks for the support to Buchsenhausen, Innsbruck, Austria.
"""

import OSC
import socket

# globals
addressManager = 0
outSocket = 0


def init():#ipAddr, port):
    """ inits manager and outsocket
    """
    createSender()
    createCallBackManager()

def createSender():
    """create and return outbound socket"""
    global outSocket
    outSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def createCallBackManager():
    global addressManager
    addressManager = OSC.CallbackManager()

def createListener(ipAddr, port):
    """create and return an inbound socket
    """
    l = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    l.bind((ipAddr, port))
    l.setblocking(0) # if not waits for msgs to arrive blocking other events
    return l

def bind(func, oscaddress):
    """ bind certains oscaddresses with certain functions in address manager
    """
    addressManager.add(func, oscaddress)

#################################

def createBinaryMsg(oscAddress, dataArray):
    """create and return general type binary OSC msg"""
    m = OSC.OSCMessage()
    m.setAddress(oscAddress)

    for x in dataArray:  ## append each item of the array to the message
        m.append(x)

    return m.getBinary() # get the actual OSC to send

def sendOSC(stufftosend, ipAddr, port): # outSocket, 
    """ send OSC msg or bundle as binary"""
    outSocket.sendto(stufftosend, (ipAddr, port))

####################################################### user interface below:

############################### send message

def sendMsg(oscAddress, dataArray, ipAddr, port):#, outSocket):
    """create and send normal OSC msgs"""
    msg = createBinaryMsg(oscAddress, dataArray)
    sendOSC(msg, ipAddr, port)  # outSocket, 

############################### bundle stuff + send bundle

def createBundle():
    """create bundled type of OSC messages"""
    b = OSC.OSCMessage()
    b.setAddress("")
    b.append("#bundle")
    b.append(0)
    b.append(0)
    return b

def appendToBundle(bundle, oscAddress, dataArray):
    """create OSC mesage and append it to a given bundle"""
    OSCmsg = createBinaryMsg(oscAddress, dataArray)
    bundle.append(OSCmsg, 'b')

def sendBundle(bundle, ipAddr, port):#, outSocket):
    """convert bundle to a binary and send it"""
    sendOSC(bundle.message, ipAddr, port) # outSocket

################################ receive osc from The Other.

def getOSC(inSocket):#, addressManager):
    """try to get incoming OSC and send it to callback manager (for osc addresses)"""
    try:
        while 1:
            data = inSocket.recv(1024)
            addressManager.handle(data)
    except:
        return "nodata" # not data arrived
################################




if __name__ == '__main__':


# example of how to use oscAPI
# the following would typically be done in your main program,
# but calling the functions here above.

    init()
    inSocket = createListener("127.0.0.1", 9001)

    # add addresses to callback manager
    def printStuff(msg):
        """deals with "print" tagged OSC addresses """

        print "printing in the printStuff function ", msg
        print "the oscaddress is ", msg[0]
        print "the value is ", msg[2]

    bind(printStuff, "/test")

    #send normal msg
    sendMsg("/test", [1, 2, 3], "127.0.0.1", 9000)

    # create and send bundle
    bundle = createBundle()
    appendToBundle(bundle, "/testing/bundles", [1, 2, 3])
    appendToBundle(bundle, "/testing/bundles", [4, 5, 6])
    sendBundle(bundle, "127.0.0.1", 9000)

    # receive OSC
    getOSC(inSocket)







