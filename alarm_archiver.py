#!/usr/bin/env python2

# alarm_archiver - Archive all alarm messages as articles. 
# 
# Copyright (C) 2001  Peter Åstrand <astrand@lysator.liu.se>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License. 
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


import kom
import select
import string

TARGET_CONFERENCE = 10176
AGENT_PERSON = 10175
AGENT_PASSWORD = "dethemligalösenordet"
KOMSERVER = "kom.lysator.liu.se"
SUBJECT = "Alarmmeddelande från %s"
MAX_CONFERENCE_LEN = 37
VERSION = "0.0"


def reformat_text(text):
    linelist = string.split(text, "\n")
    result = ""
    outline = ""
    for line in linelist:
        # Clear outline
        outline = ""
        rest = string.split(line)

        while rest:
            newword = rest[0]
            # Remove newword from rest
            rest = rest[1:]
            # The 1 is for the space. 
            if (len(outline) + 1 + len(newword)) > 70:
                # We can't get this word also. Break line here. 
                result = result + outline + "\n"
                outline = newword
            else:
                # Add newword to current line.
                # Only add space if not first word on line. 
                if outline:
                    outline = outline + " " 
                outline = outline + newword

        # Ok, this inputline is done. Add it to output. 
        result = result + outline + "\n"

    return result


def get_pers_name(num):
    "Get persons name"
    return conn.conf_name(num, default="Person %d (does not exist)")[:MAX_CONFERENCE_LEN]


def write_article(sender, subject, text):
    misc_info = kom.CookedMiscInfo()
    misc_info.recipient_list.append(kom.MIRecipient(kom.MIR_TO,
                                                    TARGET_CONFERENCE))
    misc_info.recipient_list.append(kom.MIRecipient(kom.MIR_TO, sender))

    aux_items = []
    kom.ReqCreateText(conn, subject + "\n" + reformat_text(text),
                      misc_info, aux_items).response()

def async_message(msg, c):
    if msg.recipient:
        # Not alarm message
        return

    subject = SUBJECT % get_pers_name(msg.sender)
    print "Creating article with subject:"
    print subject
    write_article(msg.sender, subject, msg.message)
    

def setup_asyncs(conn):
        conn.add_async_handler(kom.ASYNC_SEND_MESSAGE, async_message)
        kom.ReqAcceptAsync(conn, [kom.ASYNC_SEND_MESSAGE,]).response()


conn = kom.CachedConnection(KOMSERVER, 4894, "alarm_archiver")
kom.ReqLogin(conn, AGENT_PERSON, AGENT_PASSWORD, invisible = 1).response()
setup_asyncs(conn)
kom.ReqSetClientVersion(conn, "alarm_archiver.py", VERSION)

while 1:
    select.select([conn.socket], [], [])
    conn.parse_present_data()
    
