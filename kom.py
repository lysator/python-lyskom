# LysKOM Protocol A version 10 client interface for Python
# $Id: kom.py,v 1.1 1999/07/11 19:47:52 kent Exp $
# (C) 1999 Kent Engström. Released under GPL.

import socket

#
# Variables
#

whitespace = " \t\r\n"
digits = "01234567890"
ord_0 = ord("0")

#
# Connection
#

class Connection:
    # INITIALIZATION ETC.

    def __init__(self, host, port = 4894, user = ""):
        # Create socket and connect
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(host, port)

        # Create receive buffer
        self.rb = ""    # Buffer for data received from socket
        self.rb_len = 0 # Length of the buffer
        self.rb_pos = 0 # Position of first unread byte in buffer

        # Send initial string 
        self.send_string("A%dH%s\n" % (len(user), user))

        # Wait for answer "LysKOM\n"
        resp = self.receive_string(7) # FIXME: receive line here
        if resp <> "LysKOM\n":
            raise ValueError # FIXME: KOM Error here

    # LOW LEVEL ROUTINES FOR SENDING AND RECEIVING

    # Send a raw string
    def send_string(self, s):
        print ">>>",s
        self.socket.send(s)

    # Ensure that there are at least N bytes in the receive buffer
    # FIXME: Rewrite for speed and clarity
    def ensure_receive_buffer_size(self, size):
        present = self.rb_len - self.rb_pos 
        while present < size:
            needed = size - present
            wanted = max(needed,128) # FIXME: Optimize
            print "Only %d chars present, need %d: asking for %d" % \
                  (present, size, wanted)
            data = self.socket.recv(wanted)
            print "<<<", data
            self.rb = self.rb[self.rb_pos:] + data
            self.rb_pos = 0
            self.rb_len = len(self.rb)
            present = self.rb_len
        print "%d chars present (needed %d)" % \
              (present, size)
            
    # Get a string from the receive buffer (receiving more if necessary)
    def receive_string(self, len):
        self.ensure_receive_buffer_size(len)
        res = self.rb[self.rb_pos:self.rb_pos+len]
        self.rb_pos = self.rb_pos + len
        return res

    # Get a character from the receive buffer (receiving more if necessary)
    # FIXME: Optimize for speed
    def receive_char(self):
        self.ensure_receive_buffer_size(1)
        res = self.rb[self.rb_pos]
        self.rb_pos = self.rb_pos + 1
        return res

    # Skip whitespace (return first non-ws character)
    def skip_whitespace(self):
        c = self.receive_char()
        while c in whitespace:
            c = self.receive_char()
        return c

    # Get an integer from the receive buffer
    def receive_int(self):
        c = self.skip_whitespace()
        n = 0
        while c not in whitespace:
            if c not in digits:
                raise ValueError # FIXME
            print "RI used",c
            n = n * 10 + (ord(c) - ord_0)
            c = self.receive_char()
        return n
    
#
# CachedConnection
#

class CachedConnection(Connection):
    pass

# TEST

c = CachedConnection("localhost")
c.send_string("1 62 7 2Hem 1\n")
print c.receive_char()
print c.receive_int()
