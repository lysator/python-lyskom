# Locking version of shelve
# $Id: lockingshelve.py,v 1.1 1999/07/19 16:31:11 kent Exp $
# (C) 1999 Kent Engström. Released under GPL.
# NOTE! Just enough for the needs of komimportmail. Use with caution.

import shelve
import lockfile

class LockingShelve:
    def __init__(self, shelf_name):
        self.shelf_name = shelf_name
        self.lock = lockfile.Lock(shelf_name + ".lock")

    def __open_read(self):
        self.lock.shared_lock()
        self.shelf = shelve.open(self.shelf_name)

    def __open_write(self):
        self.lock.exclusive_lock()
        self.shelf = shelve.open(self.shelf_name)

    def __close(self):
        self.shelf.close()
        self.shelf = None
        self.lock.unlock()

    def keys(self):
        self.__open_read()
        try:
            return self.shelf.keys()
        finally:
            self.__close()
            
    def __getitem__(self, index):
        self.__open_read()
        try:
            return self.shelf[index]
        finally:
            self.__close()
            
    def __setitem__(self, index, data):
        self.__open_write()
        try:
            self.shelf[index] = data
            import time
        finally:
            self.__close()
            
            
