# -*- coding: iso-8859-1 -*-
# Utility routines for connection setup (replaces komparam.py)
# $Id: komconnect.py,v 1.1 2003/09/02 18:19:01 kent Exp $
# (C) 1999,2003 Kent Engström. Released under GPL.

import getpass
import sys
import optparse # Requires Python 2.3

import kom


# FIXME: Things to support in this module if needed:
# -) port numbers added to the server name ("kom.foo.bar:4894")
# -) environment variables (KOMSERVER, KOMNAME, KOMPASSWORD)
# -) ~/.komrc

# Error reporting
class Error(Exception): pass

# Add standard server, name and password arguments to an optparse
# option parser.

def add_server_name_password(parser):
    ogrp = optparse.OptionGroup(parser, "Connection Options")
    ogrp.add_option("--server",
                    help="connect to SERVER")
    ogrp.add_option("--name",
                    help="login as NAME")
    ogrp.add_option("--password",
                    help="authenticate using PASS", metavar="PASS")
    parser.add_option_group(ogrp)

# Connect and login using the information in an optparse options object
# (e.g. one set up using add_server_name_password)
def connect_and_login(options, connection_class = kom.CachedConnection):

    # Get server
    server = options.server
    if server is None:
        raise Error, "server not specified"

    # Get name
    name = options.name
    if name is None:
        raise Error, "name not specified"

    # Get password
    password = options.password
    if password is None:
        password = getpass.getpass("Password for %s on %s: " % (name,
                                                                server))

    # Connect
    try:
        conn = connection_class(server)
    except:
        (t, v, tb) = sys.exc_info()
        raise Error, "failed to connect (%s)" % t

    # Lookup name
    persons = conn.lookup_name(name, want_pers = 1, want_confs = 0)
    if len(persons) == 0:
        raise Error, "name not found"
    elif len(persons) <> 1:
        raise Error, "name not unique"
    person_no = persons[0][0]
    
    # Login
    try:
        kom.ReqLogin(conn, person_no, password).response()
    except kom.Error:
        (t, v, tb) = sys.exc_info()
        raise Error, "failed to log in (%s)" % t

    # Done!
    return conn
