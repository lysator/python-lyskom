#!/usr/bin/python

# Demonstrates use of threaded LysKOM interface.
# Messages are handled by new threads.

import kom
import thkom
import sys
import string
import thread

plock = thread.allocate_lock()

def handlemsg(msg, c):
   recr = kom.ReqGetUconfStat(c, msg.recipient)
   senr = kom.ReqGetUconfStat(c, msg.sender)
   recn = recr.response().name
   senn = senr.response().name

   plock.acquire()
   print "------------------------------------------------------------"
   print "Från", senn
   print "Till", recn
   print
   print msg.message
   print "------------------------------------------------------------"
   plock.release()
   
def main():
   c = thkom.ThreadedConnection("kom.lysator.liu.se")
   kom.ReqLogin(c, string.atoi(sys.argv[1]), sys.argv[2], 1).response()
   print "Logged in!"
   c.add_async_handler(kom.ASYNC_SEND_MESSAGE, handlemsg)
   kom.ReqAcceptAsync(c, [kom.ASYNC_SEND_MESSAGE]).response()
   l = thread.allocate_lock()
   l.acquire()
   l.acquire()
   
if __name__ == "__main__": main()
