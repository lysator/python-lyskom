#!/usr/bin/python
# Show some information around unread letters (or articles)
# $Id: komunread.py,v 1.2 2001/01/02 09:37:28 kent Exp $
# (C) 1999 Kent Engström. Released under GPL.

import kom
import komparam
import sys
import getopt
import string

# Get revision number from RCS/CVS
vc_revision = "$Revision: 1.2 $"
revision = vc_revision[11:-2]

# Error/sucess reporting
exit_code = 0
def error(str, code = 2, exit_now = 0):
    global exit_code
    exit_code = max(exit_code, code)
    sys.stderr.write("ERROR: " + str + "\n")
    if exit_now:
        exit()
        
def success(str):
    sys.stderr.write("OK: " + str + "\n")

def exit():
    sys.exit(exit_code)

# MAIN
# Connect and log in

param = komparam.Parameters(sys.argv[1:])
(conn, conn_error) = param.connect_and_login(kom.CachedConnection)
if conn is None:
    sys.stderr.write("%s: %s\n" % (sys.argv[0], conn_error))
    sys.exit(1)

#
# CHECK FOR OPTIONS
#

conference = None

options, arguments = getopt.getopt(param.get_arguments(),
                                   "",
                                   ["conference="])

for (opt, optarg) in options:
    if opt == "--conference":
        matches = conn.lookup_name(optarg, 1, 1)
        if len(matches) == 0:
            error("%s -- conference not found" % optarg)
        elif len(matches) <> 1:
            error("%s -- ambiguous recipient" % optarg)
        else:
            conference = matches[0][0]
    else:
        error("Option %s not handled (internal error)" % opt, exit_now = 1)

if conference is None:
    conference = param.get_person_no()
    
unread_texts = conn.get_unread_texts(param.get_person_no(),
                                         conference)

for (loc_no, global_no) in unread_texts:
    ts = conn.textstats[global_no]

    author = conn.conf_name(ts.author)
    print "%7d /%s/ %s" % \
          (loc_no,
           ts.creation_time.to_date_and_time(),
           author)
    print "%7d %s" % (global_no, conn.subjects[global_no])
    print

# Exit successfully
exit()

