# Primitive lock file handling 
# $Id: lockfile.py,v 1.2 1999/10/09 14:18:55 kent Exp $
# (C) 1999 Kent Engström. Released under GPL.
# NOTE! Just enough for the needs of lockingshelve. Use with caution.

import os
import fcntl

class Lock:

    def __init__(self, lock_filename):
        self.filename = lock_filename
        self.fd = os.open(self.filename, os.O_RDWR|os.O_CREAT)
        
    def shared_lock(self):
        fcntl.flock(self.fd, fcntl.LOCK_SH)

    def exclusive_lock(self):
        fcntl.flock(self.fd, fcntl.LOCK_EX)
        
    def unlock(self):
        fcntl.flock(self.fd, fcntl.LOCK_UN)
        
        
