#!/usr/bin/python

import sys
import os
import socket
import time
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
    MBOX_LASTTIME_AUX = 25438
    
    def __init__(self, c, servant, master):
	self.c = c
	self.servant = servant
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

	# No new mail, we're done
	if not mailp:
	    return

	# User not active, we're also done
	if not self.is_active():
	    return

	# Find the last rcpt time we reported in this file

	lasttime = 0
	delaux = []
	conf = kom.ReqGetConfStat(self.c, self.servant).response()
	for aux in conf.aux_items:
	    if aux.tag == self.MBOX_LASTTIME_AUX and not aux.flags.deleted:
		if len(delaux) < 64:
		    delaux.append(aux.aux_no)
		try:
		    lasttime = string.atoi(aux.data)
		except ValueError:
		    pass
	
	# if lasttime is later than now, reset it
	if time.time() < lasttime:
	    lasttime = 0
	    
	# Extract all the new From: and Subject: lines
	f = open(mbox)
	lines = f.readlines()

	msg = ['New mail on %s:\n\n' % socket.gethostname()]

	maxtime = lasttime
	addlines = 0
	for line in lines:
	    if line[:5] == 'From ':
		addlines = 0
		try:
		    mailtt = time.strptime(line[-21:], ' %b %d %H:%M:%S %Y')
		    mailtime = int(time.mktime(mailtt))
		    if lasttime < mailtime:
			addlines = 1
			if maxtime < mailtime:
			    maxtime = mailtime
		except ValueError:
		    raise

	    if addlines:
		if string.lower(line[:5]) == 'from:' \
		   or string.lower(line[:8]) == 'subject:':
		    msg.append(line)

	if len(msg) > 1:
	    # Send message to master
	    kom.ReqSendMessage(self.c, self.master,
			       string.join(msg, '')).response()

	    # Update last time in mbox
	    aux = kom.AuxItem(self.MBOX_LASTTIME_AUX, str(maxtime))
	    kom.ReqModifyConfInfo(self.c, self.servant, delaux, [aux]).response()

    
def main():
    try:
	master = string.atoi(sys.argv[1])
	servant = string.atoi(sys.argv[2])
	passwd = sys.argv[3]
    except (ValueError, IndexError):
	print "Usage: %s master servant passwd" % sys.argv[0]
	sys.exit(1)

    c = LatentConnection('kom.lysator.liu.se', 'butler', servant, passwd)
    t = Tasks(c, servant, master)
    t.check_mbox()

if __name__ == "__main__":
    main()
