#!/usr/bin/env python2

# invite-all - Invite *all* users to a certain conference. 
#
# Copyright (C) 2002  Peter Åstrand <astrand@lysator.liu.se>
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

AGENT_PERSON = "someperson"
AGENT_PASSWORD = "somesecret"
KOMSERVER = "localhost"
INVITE_CONF = "My new conference"

import kom
import select
import string
import sys

VERSION = "0.0"

conn = kom.CachedConnection(KOMSERVER, 4894, "invite-all")

# Lookup agent user
lookup_result = kom.ReqLookupZName(conn, AGENT_PERSON, want_pers = 1).response()
if len(lookup_result) < 1:
    print "Agent user not found"
    sys.exit(1)
elif len(lookup_result) > 2:
    print "Agent username ambigious"
    sys.exit(1)

agent_person_no = lookup_result[0].conf_no

# Login
kom.ReqLogin(conn, agent_person_no, AGENT_PASSWORD, invisible = 1).response()
kom.ReqSetClientVersion(conn, "invite-all", VERSION)

# Lookup conference number
lookup_result = kom.ReqLookupZName(conn, INVITE_CONF, want_confs = 1).response()
if len(lookup_result) < 1:
    print "Conference not found"
    sys.exit(1)
elif len(lookup_result) > 2:
    print "Conference name ambigious"
    sys.exit(1)

invite_conf_no = lookup_result[0].conf_no

# Get all persons
all_persons = kom.ReqLookupZName(conn, "", want_pers = 1).response()

# Invite all persons
for pers in all_persons:
    print "Inviting", pers.name
    person_no = pers.conf_no
    mstype = kom.MembershipType()
    mstype.invitation = 1
    kom.ReqAddMember(conn, invite_conf_no, person_no, 100, 100, mstype)
