# LysKOM Protocol A version 10 client interface for Python
# $Id: komparam.py,v 1.4 1999/10/18 10:21:57 kent Exp $
# (C) 1999 Kent Engström. Released under GPL.

# Handle connection and login in a common way. Parameters are
# searched for in the following order:
# 1) Command line arguments (NOT DONE YET)
# 2) Environment variables
# 3) ~/.komrc file

import sys
import os
import string
import kom

class Parameters:
    # Stash away paramers for later us
    # (argv should typically be sys.argv[1:])
    def __init__(self, argv):
        self.argv = argv
        self.environ = os.environ
        self.file_dict = None

    # Connect and log in using parameters stored by the constructor
    # (connection_class should be kom.Connection or a subclass)
    # Return (connection object, None) on success or
    #        (None, error string) on failure
    def connect_and_login(self, connection_class):
        # Connect
        server = self.get_server()
        port = self.get_port()
        if server is None:
            return (None, "server not specified")
        try:
            conn = connection_class(server, port)
        except:
            return (None, "failed to connect to %s:%d" % (server, port))

        # Lookup name
        name = self.get_name()
        if server is None:
            return (None, "name not specified")
        persons = conn.lookup_name(name, want_pers = 1, want_confs = 0)
        if len(persons) == 0:
            return (None, "name doesn't match anybody")
        elif len(persons) <> 1:
            return (None, "name matches %d persons" % len(persons))
        self.person_no = persons[0][0]
        
        # Login
        password = self.get_password()
        if password is None:
            return (None, "password not specified")
        try:
            kom.ReqLogin(conn, self.person_no, password).response()
        except:
            return (None, 'failed to log in as "%s"' % persons[0][1])

        # Done!
        return (conn, None)

    # Get remaining arguments (after we remove our special arguments)
    def get_arguments(self):
        return self.argv[:] # FIXME!
    
    # Get person_no
    def get_person_no(self):
        return self.person_no
    
    # Semi-public interface
    
    def get_server(self):
        data = self.get_parameter("KOMSERVER", "server")
        if data is not None:
            colon_pos = string.find(data, ":")
            if colon_pos <> -1:
                data = data[:colon_pos]
        return data
    
    def get_port(self):
        data = self.get_parameter("KOMSERVER", "server")
        if data is not None:
            colon_pos = string.find(data, ":")
            if colon_pos <> -1:
                data = data[colon_pos+1:]
        try:
            return string.atoi(data)
        except:
            return 4894

    def get_name(self):
        return self.get_parameter("KOMNAME", "name")

    def get_password(self):
        return self.get_parameter("KOMPASSWORD", "password")

    # Private
    
    def get_parameter(self, env_name, file_name):
        # In environment?
        if self.environ.has_key(env_name):
            return self.environ[env_name]

        # In file?
        self.ensure_file_loaded()
        if self.file_dict.has_key(file_name):
            return self.file_dict[file_name]

        return None

    def ensure_file_loaded(self):
        # Do not load twice
        if self.file_dict is not None:
            return

        # Load file
        self.file_dict = {}
        try:
            f = open("%s/.komrc" % os.environ["HOME"])
            lines = f.readlines()
            f.close()
            
            for line in lines:
                list = map(string.strip,string.split(line,"="))
                if len(list) == 2:
                    self.file_dict[list[0]] = list[1]
                pass
        except:
            pass
