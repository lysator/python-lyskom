# Support for reading, decoding and decomposing MIME messages.
# $Id: mimereader.py,v 1.4 2001/01/15 22:04:00 kent Exp $
# (C) 1999 Kent Engström. Released under GPL.

# This module is primarily designed for use with komimportmail,
# but should be useful in other situations too.

# Note: Python 1.5.2 is needed because we need to call
# multifile.MultiFile with seekable = 0.

import mimetools
import multifile
import string
import cStringIO
import os
import rfc1522

# This class represents a mail message in MIME format or basic RFC 822
# format. Attributes:
# - headers: mimetools.Message object encapsulating the message headers 
# - data: the Part object corresponding to the message body

class Message:
    # Initialize and read the message from a file object
    def __init__(self, infile):
        self.headers = mimetools.Message(infile, seekable = 0)
        if self.headers.has_key("MIME-Version"):
            # MIME message (we foolishly disregard the version number)
            self.mime = 1
            if self.headers.getmaintype() == "multipart":
                self.data = MultiPart(self.headers, infile)
            else:
                self.data = DiscretePart(self.headers, infile)
        else:
            # RFC 822 message
            self.mime = 0
            self.data = DiscretePart(self.headers, infile,
                                     maintype ="text",
                                     subtype = "plain")

    # Return a string describing the structure of the message
    def show_structure(self):
        if self.mime:
            head = "MIME message consisting of:"
        else:
            head = "RFC822 message consisting of:"
        return head + "\n" + self.data.show_structure(1)

    # Return a linear list of all discrete parts
    def linear_list_of_discrete_parts(self):
        return self.data.linear_list_of_discrete_parts()

    # Remove redundant HTML parts
    def remove_redundant_html(self):
        self.data.remove_redundant_html()


# Common attributes and methods for a MIME part (discrete or multipart)
class Part:
    def __init__(self, headers, infile, maintype = None, subtype = None):
        self.headers = headers

        if maintype is not None:
            self.maintype = maintype
        else:
            self.maintype = headers.getmaintype()
            
        if subtype is not None:
            self.subtype = subtype
        else:
            self.subtype = headers.getsubtype()

    def __getitem__(self, key):
        # Delegate to self.headers, but remove RFC1522 coding
        return rfc1522.decode(self.headers[key])
            
# Attributes of a discrete part
# - maintype, subtype: MIME type
# - headers: mimetools.Message object encapsulating the headers of the part
# - data: the body of the part as one string

class DiscretePart(Part):
    def __init__(self, headers, infile, maintype = None, subtype = None):
        Part.__init__(self, headers, infile, maintype, subtype)
        if self.maintype == "multipart": raise ValueError

        encoding = self.headers.getencoding()
        if encoding in ["base64", "quoted-printable"]:
            # Decode using method in mimetools module
            csio = cStringIO.StringIO()
            mimetools.decode(infile, csio, encoding)
            self.data = csio.getvalue()
            csio.close()
        else:
            # Unknown coding or 7bit/8bit/binary: just read it
            self.data = infile.read()

        # If the content type is text, convert CRLF to LF
        # FIXME: does this create problems? Restrict to text/plain?
        if self.maintype == "text":
            self.data = string.replace(self.data, "\r\n", "\n")

    def __repr__(self):
        return "<%s/%s, size: %d>" % \
               (self.maintype, self.subtype, len(self.data))

    def show_structure(self, level):
        return "%s- %s/%s (%d bytes)\n" % \
               (" " * (level * 4),
                self.maintype, self.subtype,
                len(self.data))
        
    def linear_list_of_discrete_parts(self):
        return [self]

    # Remove redundant HTML parts
    def remove_redundant_html(self):
        pass


# Attributes of a multipart
# - maintype, subtype: MIME type
# - headers: mimetools.Message object encapsulating the headers of the part
# - parts: list of Part objects

class MultiPart(Part):
    def __init__(self, headers, infile, maintype = None, subtype = None):
        Part.__init__(self, headers, infile, maintype, subtype)
        if self.maintype <> "multipart": raise ValueError
        self.parts = []
        
        boundary = headers.getparam("boundary")
        if boundary is None:
            # They are cheating on us! Try to survive.
            boundary = "=-=-=-EmergencyBoundary%d" % os.getpid()
            
        mf = multifile.MultiFile(infile, seekable = 0)
        mf.push(boundary)

        # We should skip all data before the first section marker,
        # so the loop condition below works.
        while mf.next():
            subheaders = mimetools.Message(mf)

            if subheaders.getmaintype() == "multipart":
                self.parts.append(MultiPart(subheaders, mf))
            else:
                self.parts.append(DiscretePart(subheaders, mf))
        mf.pop()

    def __repr__(self):
        return "<%s/%s, parts: %d>" % \
               (self.maintype, self.subtype, len(self.parts))

    def show_structure(self, level):
        return "%s- %s/%s (%d parts)\n" % \
               (" " * (level * 4),
                self.maintype, self.subtype,
                len(self.parts)) + \
                string.join(map(lambda x, l=level + 1: x.show_structure(l),
                                self.parts),
                            "")
    def linear_list_of_discrete_parts(self):
        ll = []
        for p in self.parts:
            ll = ll + p.linear_list_of_discrete_parts()
        return ll
    

    # Remove redundant HTML parts
    def remove_redundant_html(self):
        # For the moment, concentrate on the most common case:
        # - a multipart/alternative with first text/plain, then text/html
        if self.subtype ==  "alternative" and \
           len(self.parts) == 2 and \
           self.parts[0].maintype == self.parts[1].maintype == "text" and \
           self.parts[0].subtype == "plain" and \
           self.parts[1].subtype == "html":
            del self.parts[1]
        else:
            for p in self.parts:
                p.remove_redundant_html()
           

