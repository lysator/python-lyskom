# Support for reading, decoding and decomposing MIME messages.

import mimetools
import multifile
import string
import cStringIO
import os

# This class represents a mail message in MIME format or basic RFC 822
# format.

class Message:
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

    def show_structure(self):
        if self.mime:
            head = "MIME message consisting of:"
        else:
            head = "RFC822 message consisting of:"
        return head + "\n" + self.data.show_structure(1)

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

    def show_structure(self, level):
        return "%s- %s/%s (%d bytes)\n" % \
               (" " * (level * 4),
                self.maintype, self.subtype,
                len(self.data))
        
        
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
            
        mf = multifile.MultiFile(infile)
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
        
    def show_structure(self, level):
        return "%s- %s/%s (%d parts)\n" % \
               (" " * (level * 4),
                self.maintype, self.subtype,
                len(self.parts)) + \
                string.join(map(lambda x, l=level + 1: x.show_structure(l),
                                self.parts),
                            "")
