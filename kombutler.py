#!/usr/bin/python

import sys
import os
import socket
import string
from stat import *

import kom

class LatentConnection(kom.Connection):
    def __init__(self, server, connuser, userno, password):
	self.__server = server
	self.__connuser = connuser
	self.__userno = userno
	self.__password = password
	self.__connected = 0

    def register_request(self, req):
	if not self.__connected:
	    kom.Connection.__init__(self, self.__server, user = self.__connuser)
	    self.__connected = 1
	    kom.ReqLogin(self, self.__userno, self.__password).response()

	return kom.Connection.register_request(self, req)


class Tasks:
    def __init__(self, c, master):
	self.c = c
	self.master = master
	self.master_active = -1

    def is_active(self):
	if self.master_active == -1:
	    self.master_active = 0
	    sessions = kom.ReqWhoIsOnDynamic(self.c, active_last = 15 * 60).response()
	    for s in sessions:
		if s.person == self.master:
		    self.master_active = 1
		    break

	return self.master_active

    def check_mbox(self):
	mbox = os.environ['MAIL']

	mailp = 0
	try:
	    s = os.stat(mbox)
	    if S_ISREG(s[ST_MODE]) and s[ST_SIZE] > 0:
		if s[ST_MTIME] >= s[ST_ATIME] or s[ST_CTIME] >= s[ST_ATIME]:
		    mailp = 1
	except os.error:
	    pass

	# No new mail, die
	if not mailp:
	    return

	if self.is_active():
	    kom.ReqSendMessage(self.c, self.master, 'New mail on %s' % socket.gethostname()).response()
	    open(mbox).read(1)

    
def main():
    try:
	master = string.atoi(sys.argv[1])
	servant = string.atoi(sys.argv[2])
	passwd = sys.argv[3]
    except (ValueError, IndexError):
	print "Usage: efforum [-c] [-n #] master servant passwd"
	sys.exit(1)

    c = LatentConnection('kom.lysator.liu.se', 'butler', servant, passwd)
    t = Tasks(c, master)
    t.check_mbox()

if __name__ == "__main__":
    main()
