# -*- coding: iso-8859-1 -*-
# Handling of RFC1522 coding in mail headers
# $Id: rfc1522.py,v 1.5 2003/11/13 20:36:16 kent Exp $
# (C) 1999 Kent Engström. Released under GPL.

# NOTE! Just enough for the needs of komimportmail. Use with caution.
# The following limitations/bugs are evident:
# - only some character sets are considered for decoding
# - only QP (not Base64) is decoded

import re
import string
import base64
import quopri
import cStringIO

decodable_charsets = ["ISO-8859-1","US-ASCII"]
re_coded = re.compile("=\?([^?]*)\?([qQbB])\?([^?]*)\?=")

def decode(str):
    # Scan the input string, converting QP/Base64-coded parts to normal
    # 8-bit strings.
    # Example: "=?ISO-8859-1?Q?Sm=E5_r=E4ksm=F6rg=E5sar?="
    # will become "Små räksmörgåsar"

    start = 0
    while start is not None:
        m = re_coded.search(str, start)
        if not m:
            break

        (charset, coding, data) = m.group(1,2,3)
        if string.upper(charset) not in decodable_charsets:
            start = m.end(0)
            continue # Look for more coded parts to try to convert

        if coding in "qQ":
            decoded = decode_qp(string.replace(data, "_", " "))
        else:
            decoded = base64.decodestring(data)
        str = str[:m.start(0)] + decoded + str[m.end(0):]
        start = m.start(0) + len(decoded)

    return str

def decode_qp(str):
    # The quopri modules does not provide string versions of the functions
    infile = cStringIO.StringIO(str)
    outfile = cStringIO.StringIO()
    quopri.decode(infile, outfile)
    return outfile.getvalue()
