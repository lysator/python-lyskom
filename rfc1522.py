# Handling of RFC1522 coding in mail headers
# $Id: rfc1522.py,v 1.2 1999/07/19 18:37:05 kent Exp $
# (C) 1999 Kent Engström. Released under GPL.

# NOTE! Just enough for the needs of komimportmail. Use with caution.
# The following limitations/bugs are evident:
# - only some character sets are considered for decoding
# - only QP (not Base64) is decoded

import re
import string

decodable_charsets = ["ISO-8859-1","US-ASCII"]
re_coded = re.compile("=\?([^?]*)\?[qQ]\?([^?]*)\?=")

def decode(str):
    # Scan the input string, converting QP-coded parts to normal
    # 8-bit strings.
    # Example: "=?ISO-8859-1?Q?Sm=E5_r=E4ksm=F6rg=E5sar?="
    # will become "Små räksmörgåsar"

    start = 0
    while start is not None:
        m = re_coded.search(str, start)
        if not m:
            break

        (charset, data) = m.group(1,2)
        if string.upper(charset) not in decodable_charsets:
            start = m.end(0)
            continue # Look for more coded parts to try to convert

        decoded = decode_qp(data)
        str = str[:m.start(0)] + decoded + str[m.end(0):]
        start = m.start(0) + len(decoded)

    return str

def decode_qp(str):
    # Decode the input string from QP to normal 8-bit text, handling both
    # "=HH" (hex coded) and "_" (space).

    res = []
    i = 0
    while i < len(str):
        if str[i] == "_":
            res.append(" ")
        elif str[i] == "=" and i < len(str) - 2 and \
             str[i+1] in string.hexdigits and str[i+2] in string.hexdigits:
            res.append(chr(eval("0x" + str[i+1:i+3])))
            i = i + 2
        else:
            res.append(str[i])
        i = i + 1
    return string.join(res,"")
                
