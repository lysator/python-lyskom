#!/usr/bin/python
# Show unread letters
# $Id: komunread.py,v 1.1 1999/07/23 18:16:33 kent Exp $
# (C) 1999 Kent Engström. Released under GPL.

import kom
import komparam
import sys
import getopt
import string

# Get revision number from RCS/CVS
vc_revision = "$Revision: 1.1 $"
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

#
# Get unread texts for a certain person in a certain conference
# Return a list of tuples (local no, global no)
#
# FIXME: This should be part of CachedConnection or another
# subclass/mixin of Connection.

def get_unread_texts(person_no, conf_no):
    # Start list
    unread = []
    
    # Get membership record
    ms = kom.ReqQueryReadTexts(conn, person_no, conf_no).response()

    # Start asking for translations
    ask_for = ms.last_text_read + 1
    more_to_fetch = 1
    while more_to_fetch:
        try:
            mapping = kom.ReqLocalToGlobal(conn, conf_no,
                                           ask_for, 255).response()
            for tuple in mapping.list:
                if tuple[0] not in ms.read_texts:
                    unread.append(tuple)
                ask_for = mapping.range_end
                more_to_fetch = mapping.later_texts_exists
        except kom.NoSuchLocalText:
            # No unread texts
            more_to_fetch = 0

    return unread

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

options, arguments = getopt.getopt(param.get_arguments(),
                                   "",
                                   [
                                       ])
for (opt, optarg) in options:
    error("Option %s not handled (internal error)" % opt, exit_now = 1)

unread_texts = get_unread_texts(param.get_person_no(),
                                param.get_person_no())

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

