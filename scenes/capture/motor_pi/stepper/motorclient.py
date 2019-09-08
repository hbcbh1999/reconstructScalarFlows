#!/usr/bin/env python2

import sys
import socket
import datetime
import math
import time
from time import sleep

# The c binary for controlling the stepper motor is loaded via ctypes
from ctypes import *

stepper_lib = cdll.LoadLibrary('./stepper.so')

# buffer containing the incomplete commands
recvBuffer = str()


# all my socket messages will follow the scheme: "<Control code>|<data>~"
def sendMsg(s, msg):
    s.sendall("%s~" % msg)


# waits until a full message is received
def getMsg(s):
    global recvBuffer

    while True:

        # receive until full message
        delim = recvBuffer.find("~")
        if(delim != -1):

            # full message -> extract it and remove from buffer
            result = recvBuffer[0:delim]
            recvBuffer = recvBuffer[delim + 1:]
            return result

        try:
            currentRecv = s.recv(4096, 0)

        except KeyboardInterrupt:
            print "Keyborad interrupt -> EXIT"
            s.close()
            sys.exit(0)

        except:
            return ""

        if(len(currentRecv) == 0):
            # this means a empty string was received -> this should not happen
            return ''

        print "recv: %s" % currentRecv
        recvBuffer = recvBuffer + currentRecv


# Init the native c library
def slide_init():
    #res = stepper_lib.init()
    if res == 0:
        raise Exception("Failed to initialize stepper lib")
    slide_set(0.5)
    print "testest"


# set the slide to the given relative (0-1) position
def slide_set(pos):

    # Length of the slide in steps
    slide_length = 20000
    # Small offset to avoid the slide crashing into the end switch
    slide_min_ofs = 30

    # relative value to step value
    pos = (slide_length - slide_min_ofs) * pos + slide_min_ofs

    res = stepper_lib.set_position(c_long(int(pos)))
    if res == 0:
        raise Exception("Failed to set_position of the slide")


def main(argv):
    if len(argv) <= 1:
        # it requires one argument (the host ip)
        print "Missing arguments!\nUsage: motorclient.py <control host>"
        return

    s = socket.socket()
    host = socket.gethostbyname(argv[1])

    try:
        # connect
        s.connect((host, 54321))

        # send HI messag with CS (for "callibration slide") as client id
        # The host will store this client as a non-camera client
        sendMsg(s, "HI|CS")

        # wait for answer...
        m = getMsg(s)

        # ... and check if answer is expected
        if(m != ("CON|CS")):
            print "Invalid answer from control host: %s" % m
            return

    except:
        print "Failed to connect to control host"
        return

    slide_init()

    # main loop
    try:
        while True:
            # get a command
            msg = getMsg(s)

            # split command
            delim = msg.find("|")

            if (msg == "" or delim == -1):
                # command invalid
                print "Connection terminated or received invalid command"
                s.close()
                sys.exit(0)

            # cmd  ~ command
            # data ~ data for command
            cmd = msg[0:delim]
            data = msg[delim + 1:]

            print "CMD: \"%s\"" % cmd

            if(cmd == "EXIT"):
                # end program
                s.close()
                sys.exit(0)
            elif(cmd == "SET"):
		print "Set the slide to ", data
                # set slide position
                # the data is a float value defining the destination
                slide_set(float(data))
		sendMsg(s, "OK|SET")

    except KeyboardInterrupt:
        s.close()
        sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)

