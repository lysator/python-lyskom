#!/usr/bin/python

# Demonstrates use of threaded LysKOM interface.
# Messages are put on a queue as they are recieved

import kom
import thkom
import sys
import string
import Queue

def main():
   c = thkom.ThreadedConnection("kom.lysator.liu.se")
   kom.ReqLogin(c, string.atoi(sys.argv[1]), sys.argv[2], 1).response()
   print "Logged in!"
   q = Queue.Queue(10)
   c.add_async_handler(kom.ASYNC_SEND_MESSAGE, q)
   kom.ReqAcceptAsync(c, [kom.ASYNC_SEND_MESSAGE]).response()
   while 1:
      msg, conn = q.get()
      recr = kom.ReqGetUconfStat(c, msg.recipient)
      senr = kom.ReqGetUconfStat(c, msg.sender)
      recn = recr.response().name
      senn = senr.response().name

      print "------------------------------------------------------------"
      print "Från", senn
      print "Till", recn
      print
      print msg.message
      print "------------------------------------------------------------"
   
if __name__ == "__main__": main()