# LysKOM Protocol A version 10 client interface for Python
# $Id: kom.py,v 1.2 1999/07/12 20:40:47 kent Exp $
# (C) 1999 Kent Engström. Released under GPL.

import socket
import time

#
# Variables
#

whitespace = " \t\r\n"
digits = "01234567890"
ord_0 = ord("0")

# All errors belong to this class
class Error(Exception): pass

# All Protocol A errors are subclasses of ServerError
class ServerError(Error): pass
class NotImplemented(ServerError): pass # (2)
class ObsoleteCall(ServerError): pass # (3)
class InvalidPassword(ServerError): pass # (4)
class StringTooLong(ServerError): pass # (5)
class LoginFirst(ServerError): pass # (6)
class LoginDisallowed(ServerError): pass # (7)
class ConferenceZero(ServerError): pass # (8)
class UndefinedConference(ServerError): pass # (9)
class UndefinedPerson(ServerError): pass # (10)
class AccessDenied(ServerError): pass # (11)
class PermissionDenied(ServerError): pass # (12)
class NotMember(ServerError): pass # (13)
class NoSuchText(ServerError): pass # (14)
class TextZero(ServerError): pass # (15)
class NoSuchLocalText(ServerError): pass # (16)
class LocalTextZero(ServerError): pass # (17)
class BadName(ServerError): pass # (18)
class IndexOutOfRange(ServerError): pass # (19)
class ConferenceExists(ServerError): pass # (20)
class PersonExists(ServerError): pass # (21)
class SecretPublic(ServerError): pass # (22)
class Letterbox(ServerError): pass # (23)
class LdbError(ServerError): pass # (24)
class IllegalMisc(ServerError): pass # (25)
class IllegalInfoType(ServerError): pass # (26)
class AlreadyRecipient(ServerError): pass # (27)
class AlreadyComment(ServerError): pass # (28)
class AlreadyFootnote(ServerError): pass # (29)
class NotRecipient(ServerError): pass # (30)
class NotComment(ServerError): pass # (31)
class NotFootnote(ServerError): pass # (32)
class RecipientLimit(ServerError): pass # (33)
class CommentLimit(ServerError): pass # (34)
class FootnoteLimit(ServerError): pass # (35)
class MarkLimit(ServerError): pass # (36)
class NotAuthor(ServerError): pass # (37)
class NoConnect(ServerError): pass # (38)
class OutOfmemory(ServerError): pass # (39)
class ServerIsCrazy(ServerError): pass # (40)
class ClientIsCrazy(ServerError): pass # (41)
class UndefinedSession(ServerError): pass # (42)
class RegexpError(ServerError): pass # (43)
class NotMarked(ServerError): pass # (44)
class TemporaryFailure(ServerError): pass # (45)
class LongArray(ServerError): pass # (46)
class AnonymousRejected(ServerError): pass # (47)
class IllegalAuxItem(ServerError): pass # (48)
class AuxItemPermission(ServerError): pass # (49)
class UnknownAsync(ServerError): pass # (50)
class InternalError(ServerError): pass # (51)
class FeatureDisabled(ServerError): pass # (52)
class MessageNotSent(ServerError): pass # (53)
class InvalidMembershipType(ServerError): pass # (54)

# Mapping from Protocol A error_no to Python exception
error_dict = {
    2: NotImplemented,
    3: ObsoleteCall,
    4: InvalidPassword,
    5: StringTooLong,
    6: LoginFirst,
    7: LoginDisallowed,
    8: ConferenceZero,
    9: UndefinedConference,
    10: UndefinedPerson,
    11: AccessDenied,
    12: PermissionDenied,
    13: NotMember,
    14: NoSuchText,
    15: TextZero,
    16: NoSuchLocalText,
    17: LocalTextZero,
    18: BadName,
    19: IndexOutOfRange,
    20: ConferenceExists,
    21: PersonExists,
    22: SecretPublic,
    23: Letterbox,
    24: LdbError,
    25: IllegalMisc,
    26: IllegalInfoType,
    27: AlreadyRecipient,
    28: AlreadyComment,
    29: AlreadyFootnote,
    30: NotRecipient,
    31: NotComment,
    32: NotFootnote,
    33: RecipientLimit,
    34: CommentLimit,
    35: FootnoteLimit,
    36: MarkLimit,
    37: NotAuthor,
    38: NoConnect,
    39: OutOfmemory,
    40: ServerIsCrazy,
    41: ClientIsCrazy,
    42: UndefinedSession,
    43: RegexpError,
    44: NotMarked,
    45: TemporaryFailure,
    46: LongArray,
    47: AnonymousRejected,
    48: IllegalAuxItem,
    49: AuxItemPermission,
    50: UnknownAsync,
    51: InternalError,
    52: FeatureDisabled,
    53: MessageNotSent,
    54: InvalidMembershipType,
    }

# All local errors are subclasses of LocalError
class LocalError(Error): pass
class BadInitialResponse(LocalError): pass # Not "LysKOM\n"
class BadRequestId(LocalError): pass  # Bad request id encountered
class ProtocolError(LocalError): pass # E.g. unexpected response

#
# Classes for requests to the server are all subclasses of Request.
#
# N.B: the identifier "c" below should be read as "connection"
#

class Request:
    def register(self, c):
        self.id = c.register_request(self)
        self.c = c
        
    def response(self):
        return self.c.wait_and_dequeue(self.id)

    # Default response parser expects nothing.
    # Override when appropriate.
    def parse_response(self):
        return None

# login-old [0] (1) Obsolete (4) Use login (62)
# logout [1] (1) Recommended
class ReqLogout(Request):
    def __init__(self, c):
        self.register(c)
        c.send_string("%d 1\n" % self.id)

# change-conference [2] (1) Recommended
class ReqChangeConference(Request):
    def __init__(self, c, conf_no):
        self.register(c)
        c.send_string("%d 2 %d\n" % (self.id, conf_no))

# change-name [3] (1) Recommended
class ReqChangeName(Request):
    def __init__(self, c, conf_no, new_name):
        self.register(c)
        c.send_string("%d 3 %d %dH%s\n" % (self.id, conf_no,
                                           len(new_name), new_name))

# change-what-i-am-doing [4] (1) Recommended
class ReqChangeWhatIAmDoing(Request):
    def __init__(self, c, what):
        self.register(c)
        c.send_string("%d 4 %dH%s\n" % (self.id, len(what), what))

# get-text [25] (1) Recommended
class ReqGetText(Request):
    def __init__(self, c, text_no, start_char, end_char):
        self.register(c)
        c.send_string("%d 25 %d %d %d\n" %
                      (self.id, text_no, start_char, end_char))

    def parse_response(self):
        # --> string
        return self.c.parse_string()
    
# get-text-stat-old [26] (1) Obsolete (10) Use get-text-stat (90)

# get-time [35] (1) Recommended
class ReqGetTime(Request):
    def __init__(self, c):
        self.register(c)
        c.send_string("%d 35\n" % self.id)

    def parse_response(self):
        # --> Time
        return self.c.parse_time()
    
# login [62] (4) Recommended
class ReqLogin(Request):
    def __init__(self, c, person_no, password, invisible = 0):
        self.register(c)
        c.send_string("%d 62 %d %dH%s %d\n" %
                      (self.id, person_no, len(password), password, invisible))

# lookup-z-name [76] (7) Recommended
class ReqLookupZName(Request):
    def __init__(self, c, name, want_pers = 0, want_confs = 0):
        self.register(c)
        c.send_string("%d 76 %dH%s %d %d\n" %
                      (self.id, len(name), name, want_pers, want_confs))

    def parse_response(self):
        # --> ARRAY ConfZInfo
        return self.c.parse_array(ConfZInfo)
        pass
    
# get-text-stat [90] (10) Recommended
class ReqGetTextStat(Request):
    def __init__(self, c, text_no):
        self.register(c)
        c.send_string("%d 90 %d\n" %
                      (self.id, text_no))

    def parse_response(self):
        # --> TextStat
        return self.c.parse_text_stat()

#
# CLASSES for KOM data types
#

class Time:
    def __init__(self):
        self.seconds = None
        self.minutes = None
        self.hours = None
        self.day = None
        self.month = None
        self.year = None
        self.day_of_week = None
        self.day_of_year = None
        self.is_dst = None

    def parse(self, c):
        self.seconds = c.parse_int()
        self.minutes = c.parse_int()
        self.hours = c.parse_int()
        self.day = c.parse_int()
        self.month = c.parse_int()
        self.year = c.parse_int()
        self.day_of_week = c.parse_int()
        self.day_of_year = c.parse_int()
        self.is_dst = c.parse_int()

    def __repr__(self):
        return "<Time %04d-%02d-%02d %02d:%02d:%02d>" % \
            (self.year + 1900, self.month + 1, self.day,
             self.hours, self.minutes, self.seconds)

class ConfZInfo:
    def __init__(self):
        self.name = None
        self.type = None
        self.conf_no = None

    def __repr__(self):
        return "<ConfZInfo %d: %s>" % \
            (self.conf_no, self.name)

    def parse(self, c):
        self.name = c.parse_string()
        self.type = c.parse_int() # FIXME: Better handling
        self.conf_no = c.parse_int()

MI_RECPT=0
MI_CC_RECPT=1
MI_COMM_TO=2
MI_COMM_IN=3
MI_FOOTN_TO=4
MI_FOOTN_IN=5
MI_LOC_NO=6
MI_REC_TIME=7
MI_SENT_BY=8
MI_SENT_AT=9
MI_BCC_RECPT=15

class MiscInfo:
    def __init__(self):
        self.type = None
        self.data = None

    def parse(self, c):
        self.type = c.parse_int()
        if self.type in [MI_REC_TIME, MI_SENT_AT]:
            self.data = c.parse_time()
        else:
            self.data = c.parse_int()

    def __repr__(self):
        return "<MiscInfo %d: %s>" % (self.type, self.data)

class AuxItem:
    def __init__(self):
        self.aux_no = None
        self.tag = None
        self.creator = None
        self.created_at = None
        self.flags = None
        self.inherit_limit = None
        self.data = None

    def parse(self, c):
        self.aux_no = c.parse_int()
        self.tag = c.parse_int()
        self.creator = c.parse_int()
        self.created_at = c.parse_time()
        self.flags = c.parse_int() # FIXME
        self.inherit_limit = c.parse_int()
        self.data = c.parse_string()
     
class TextStat:
    def __init__(self):
        self.creation_time = None
        self.author = None
        self.no_of_lines = None
        self.no_of_chars = None
        self.no_of_marks = None
        self.misc_info = [] # FIXME: Better representation!
        self.aux_items = []

    def parse(self, c):
        self.creation_time = c.parse_time()
        self.author = c.parse_int()
        self.no_of_lines = c.parse_int()
        self.no_of_chars = c.parse_int()
        self.no_of_marks = c.parse_int()
        self.misc_info = c.parse_array(MiscInfo)
        self.aux_info = c.parse_array(AuxItem)
        
#
# CLASS for a connection
#

class Connection:
    # INITIALIZATION ETC.

    def __init__(self, host, port = 4894, user = ""):
        # Create socket and connect
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(host, port)

        # Requests
        self.req_id = 0      # Last used ID (i.e. increment before use)
        self.req_queue = {}  # Requests sent to server, waiting for answers
        self.resp_queue = {} # Answers received from the server
        self.error_queue = {} # Errors received from the server
        
        # Receive buffer
        self.rb = ""    # Buffer for data received from socket
        self.rb_len = 0 # Length of the buffer
        self.rb_pos = 0 # Position of first unread byte in buffer

        # Asynchronous message handlers
        self.am_handlers = {}
        
        # Send initial string 
        self.send_string("A%dH%s\n" % (len(user), user))

        # Wait for answer "LysKOM\n"
        resp = self.receive_string(7) # FIXME: receive line here
        if resp <> "LysKOM\n":
            raise BadInitialResponse

    def register_am_handler(self, msg_no, handler):
        self.am_handlers[msg_no] = handler

    # REQUEST QUEUE
    
    # Allocate an ID for a request and register it in the queue
    def register_request(self, req):
        self.req_id = self.req_id +1
        self.req_queue[self.req_id] = req
        #print "REQUEST %s REGISTERED" % req
        return self.req_id

    # Wait for a request to be answered, return response or signal error
    def wait_and_dequeue(self, id):
        while not self.resp_queue.has_key(id) and \
              not self.error_queue.has_key(id):
            #print "Request", id,"not responded to, getting some more"
            self.parse_server_message()
        if self.resp_queue.has_key(id):
            # Response
            ret = self.resp_queue[id]
            del self.resp_queue[id]
            return ret
        else:
            # Error
            (error_no, error_status) = self.error_queue[id]
            del self.error_queue[id]
            raise error_dict[error_no], error_status
    
    # PARSING SERVER MESSAGES

    # Parse one server message
    # Could be: - answer to request (begins with =)
    #           - error for request (begins with %)
    #           - asynchronous message (begins with :)
    
    def parse_server_message(self):
        ch = self.parse_first_non_ws()
        if ch == "=":
            self.parse_response()
        elif ch == "%":
            self.parse_error()
        elif ch == ":":
            self.parse_asynchronous_message()
        else:
            raise ProtocolError

    # Parse response
    def parse_response(self):
        id = self.parse_int()
        #print "Response for",id,"coming"
        if self.req_queue.has_key(id):
            # Delegate parsing to the ReqXXXX class
            resp = self.req_queue[id].parse_response()
            # Remove request and add response
            del self.req_queue[id]
            self.resp_queue[id] = resp
        else:
            raise BadRequestId, id

    # Parse error
    def parse_error(self):
        id = self.parse_int()
        error_no = self.parse_int()
        error_status = self.parse_int()
        if self.req_queue.has_key(id):
            # Remove request and add error
            del self.req_queue[id]
            self.error_queue[id] = (error_no, error_status)
        else:
            raise BadRequestId, id

    # Parse asynchronous message
    def parse_asynchronous_message(self):
        no_args = self.parse_int()
        msg_no = self.parse_int()
        if self.am_handlers.has_key(msg_no):
            self.am_handlers[msg_no](self)
        else:
            print "*** ASYNC %d UNHANDLED ***" % msg_no
            self.parse_away(no_args)
        
    # PARSING KOM DATA TYPES

    def parse_time(self):
        t = Time()
        t.parse(self)
        return t
    
    def parse_text_stat(self):
        ts = TextStat()
        ts.parse(self)
        return ts
    
    # PARSING ARRAYS

    def parse_array(self, element_class):
        len = self.parse_int()
        res = []
        if len > 0:
            left = self.parse_first_non_ws()
            if left <> "{": raise ProtocolError
            for i in range(0, len):
                obj = element_class()
                obj.parse(self)
                res.append(obj)
            right = self.parse_first_non_ws()
            if right <> "}": raise ProtocolError
        else:
            star = self.parse_first_non_ws()
            if star <> "*": raise ProtocolError
        return res

    # PARSING BASIC DATA TYPES

    # Skip whitespace and return first non-ws character
    def parse_first_non_ws(self):
        c = self.receive_char()
        while c in whitespace:
            c = self.receive_char()
        return c

    # Get an integer and next character from the receive buffer
    def parse_int_and_next(self):
        c = self.parse_first_non_ws()
        n = 0
        while c in digits:
            n = n * 10 + (ord(c) - ord_0)
            c = self.receive_char()
        return (n, c)
    
    # Get an integer from the receive buffer (discard next character)
    def parse_int(self):
        (c, n) = self.parse_int_and_next()
        return c

    # Parse a string (Hollerith notation)
    def parse_string(self):
        (len, h) = self.parse_int_and_next()
        if h <> "H": raise ProtocolError
        return self.receive_string(len)
    
    # LOW LEVEL ROUTINES FOR SENDING AND RECEIVING

    # Send a raw string
    def send_string(self, s):
        #print ">>>",s
        self.socket.send(s)

    # Ensure that there are at least N bytes in the receive buffer
    # FIXME: Rewrite for speed and clarity
    def ensure_receive_buffer_size(self, size):
        present = self.rb_len - self.rb_pos 
        while present < size:
            needed = size - present
            wanted = max(needed,128) # FIXME: Optimize
            #print "Only %d chars present, need %d: asking for %d" % \
            #      (present, size, wanted)
            data = self.socket.recv(wanted)
            #print "<<<", data
            self.rb = self.rb[self.rb_pos:] + data
            self.rb_pos = 0
            self.rb_len = len(self.rb)
            present = self.rb_len
        #print "%d chars present (needed %d)" % \
        #      (present, size)
            
    # Get a string from the receive buffer (receiving more if necessary)
    def receive_string(self, len):
        self.ensure_receive_buffer_size(len)
        res = self.rb[self.rb_pos:self.rb_pos+len]
        self.rb_pos = self.rb_pos + len
        return res

    # Get a character from the receive buffer (receiving more if necessary)
    # FIXME: Optimize for speed
    def receive_char(self):
        self.ensure_receive_buffer_size(1)
        res = self.rb[self.rb_pos]
        self.rb_pos = self.rb_pos + 1
        return res

#
# CachedConnection
#

class CachedConnection(Connection):
    pass

