# LysKOM Protocol A version 10 client interface for Python
# $Id: kom.py,v 1.7 1999/07/14 22:40:03 kent Exp $
# (C) 1999 Kent Engström. Released under GPL.

import socket
import time
import string

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
class UnimplementedAsync(LocalError): pass # Unknown asynchronous message

# Constants for Misc-Info (needed in requests below)

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

MIR_TO = MI_RECPT
MIR_CC = MI_CC_RECPT
MIR_BCC = MI_BCC_RECPT

MIC_COMMENT = MI_COMM_TO
MIC_FOOTNOTE = MI_FOOTN_TO

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

# create-person-old [5] (1) Obsolete (10) Use create-person (89)
# get-person-stat-old [6] (1) Obsolete (1) Use get-person-stat (49)

# set-priv-bits [7] (1) Recommended
class ReqSetPrivBits(Request):
    def __init__(self, c, person_no, privileges):
        self.register(c)
        c.send_string("%d 7 %d %s\n" % (self.id,
                                        person_no,
                                        privileges.to_string()))

# set-passwd [8] (1) Recommended
class ReqSetPasswd(Request):
    def __init__(self, c, person_no, old_pwd, new_pwd):
        self.register(c)
        c.send_string("%d 8 %d %dH%s %dH%s\n" % (self.id,
                                                 person_no,
                                                 len(old_pwd), old_pwd,
                                                 len(new_pwd), new_pwd))

# query-read-texts-old [9] (1) Obsolete (10) Use query-read-texts (98)
# create-conf-old [10] (1) Obsolete (10) Use create-conf (88)

# delete-conf [11] (1) Recommended
class ReqDeleteConf(Request):
    def __init__(self, c, conf_no):
        self.register(c)
        c.send_string("%d 11 %d\n" % (self.id, conf_no))

# lookup-name [12] (1) Obsolete (7) Use lookup-z-name (76)
# get-conf-stat-older [13] (1) Obsolete (10) Use get-conf-stat (91)
# add-member-old [14] (1) Obsolete (10) Use add-member (100)

# sub-member [15] (1) Recommended
class ReqSubMember(Request):
    def __init__(self, c, conf_no, person_no):
        self.register(c)
        c.send_string("%d 15 %d %d\n" % (self.id, conf_no, person_no))

# set-presentation [16] (1) Recommended
class ReqSetPresentation(Request):
    def __init__(self, c, conf_no, text_no):
        self.register(c)
        c.send_string("%d 16 %d %d\n" % (self.id, conf_no, text_no))

# set-etc-motd [17] (1) Recommended
class ReqSetEtcMoTD(Request):
    def __init__(self, c, conf_no, text_no):
        self.register(c)
        c.send_string("%d 17 %d %d\n" % (self.id, conf_no, text_no))

# set-supervisor [18] (1) Recommended
class ReqSetSupervisor(Request):
    def __init__(self, c, conf_no, admin):
        self.register(c)
        c.send_string("%d 18 %d %d\n" % (self.id, conf_no, admin))

# set-permitted-submitters [19] (1) Recommended
class ReqSetPermittedSubmitters(Request):
    def __init__(self, c, conf_no, perm_sub):
        self.register(c)
        c.send_string("%d 19 %d %d\n" % (self.id, conf_no, perm_sub))

# set-super-conf [20] (1) Recommended
class ReqSetSuperConf(Request):
    def __init__(self, c, conf_no, super_conf):
        self.register(c)
        c.send_string("%d 20 %d %d\n" % (self.id, conf_no, super_conf))

# set-conf-type [21] (1) Recommended
class ReqSetConfType(Request):
    def __init__(self, c, conf_no, type):
        self.register(c)
        c.send_string("%d 21 %d %s\n" % (self.id,
                                         conf_no,
                                         type.to_string()))

# set-garb-nice [22] (1) Recommended
class ReqSetGarbNice(Request):
    def __init__(self, c, conf_no, nice):
        self.register(c)
        c.send_string("%d 22 %d %d\n" % (self.id, conf_no, nice))

# get-marks [23] (1) Recommended
class ReqGetMarks(Request):
    def __init__(self, c):
        self.register(c)
        c.send_string("%d 23\n" % (self.id))

    def parse_response(self):
        # --> string
        return self.c.parse_array(Mark)

# mark-text-old [24] (1) Obsolete (4) Use mark-text/unmark-text (72/73)

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

# mark-as-read [27] (1) Recommended
# FIXME!

# create-text-old [28] (1) Obsolete (10) Use create-text (86)

# delete-text [29] (1) Recommended
class ReqDeleteText(Request):
    def __init__(self, c, text_no):
        self.register(c)
        c.send_string("%d 29 %d\n" % (self.id, text_no))

# add-recipient [30] (1) Recommended
class ReqAddRecipient(Request):
    def __init__(self, c, text_no, conf_no, recpt_type = MIR_TO):
        self.register(c)
        c.send_string("%d 30 %d %d %d\n" % \
                      (self.id, text_no, conf_no, recpt_type))

# sub-recipient [31] (1) Recommended
class ReqSubRecipient(Request):
    def __init__(self, c, text_no, conf_no):
        self.register(c)
        c.send_string("%d 31 %d %d\n" % \
                      (self.id, text_no, conf_no))

# add-comment [32] (1) Recommended
class ReqAddComment(Request):
    def __init__(self, c, text_no, comment_to):
        self.register(c)
        c.send_string("%d 32 %d %d\n" % \
                      (self.id, text_no, comment_to))

# sub-comment [33] (1) Obsolete (10) FIXME: Why???
class ReqSubComment(Request):
    def __init__(self, c, text_no, comment_to):
        self.register(c)
        c.send_string("%d 33 %d %d\n" % \
                      (self.id, text_no, comment_to))

# get-map [34] (1) Obsolete??? (10) Use local-to-global (103)

# get-time [35] (1) Recommended
class ReqGetTime(Request):
    def __init__(self, c):
        self.register(c)
        c.send_string("%d 35\n" % self.id)

    def parse_response(self):
        # --> Time
        return self.c.parse_object(Time)
    
# get-info-old [36] (1) Obsolete (10) Use get-info (94)

# add-footnote [37] (1) Recommended
class ReqAddFootnote(Request):
    def __init__(self, c, text_no, footnote_to):
        self.register(c)
        c.send_string("%d 37 %d %d\n" % \
                      (self.id, text_no, footnote_to))

# sub-footnote [38] (1) Recommended
class ReqSubFootnote(Request):
    def __init__(self, c, text_no, footnote_to):
        self.register(c)
        c.send_string("%d 38 %d %d\n" % \
                      (self.id, text_no, footnote_to))

# who-is-on-old [39] (1) Obsolete (9) Use get-static-session-info (84) and
#                                         who-is-on-dynamic (83)

# set-unread [40] (1) Recommended
class ReqSetUnread(Request):
    def __init__(self, c, conf_no, no_of_unread):
        self.register(c)
        c.send_string("%d 40 %d %d\n" % \
                      (self.id, conf_no, no_of_unread))

# set-motd-of-lyskom [41] (1) Recommended
class ReqSetMoTDOfLysKOM(Request):
    def __init__(self, c, text_no):
        self.register(c)
        c.send_string("%d 41 %d\n" % \
                      (self.id, text_no))

# enable [42] (1) Recommended
class ReqEnable(Request):
    def __init__(self, c, level):
        self.register(c)
        c.send_string("%d 42 %d\n" % (self.id, level))

# sync-kom [43] (1) Recommended
class ReqSyncKOM(Request):
    def __init__(self, c):
        self.register(c)
        c.send_string("%d 43\n" % (self.id))

# shutdown-kom [44] (1) Recommended
class ReqShutdownKOM(Request):
    def __init__(self, c, exit_val):
        self.register(c)
        c.send_string("%d 44 %d\n" % (self.id, exit_val))

# broadcast [45] (1) Obsolete (1) Use send-message (53)
# get-membership-old [46] (1) Obsolete (10) Use get-membership (99)
# get-created-texts [47] (1) Obsolete (10) Use map-created-texts (104)
# get-members-old [48] (1) Obsolete (10) Use get-members (101)

# get-person-stat [49] (1) Recommended
class ReqGetPersonStat(Request):
    def __init__(self, c, person_no):
        self.register(c)
        c.send_string("%d 49 %d\n" % (self.id, person_no))

    def parse_response(self):
        # --> Person
        return self.c.parse_object(Person)

# get-conf-stat-old [50] (1) Obsolete (10) Use get-conf-stat (91)

# who-is-on [51] (1) Obsolete (9)  Use who-is-on-dynamic (83) and
#                                      get-static-session-info (84)

# get-unread-confs [52] (1) Recommended
class ReqGetUnreadConfs(Request):
    def __init__(self, c, person_no):
        self.register(c)
        c.send_string("%d 52 %d\n" % (self.id, person_no))

    def parse_response(self):
        # --> ARRAY Conf-No
        return self.c.parse_array_of_int()

# send-message [53] (1) Recommended
class ReqSendMessage(Request):
    def __init__(self, c, conf_no, message):
        self.register(c)
        c.send_string("%d 53 %d %dH%s\n" %
                      (self.id, conf_no, len(message), message))

# get-session-info [54] (1) Obsolete (9) Use who-is-on-dynamic (83)

# disconnect [55] (1) Recommended
class ReqDisconnect(Request):
    def __init__(self, c, session_no):
        self.register(c)
        c.send_string("%d 55 %d\n" %
                      (self.id, session_no))

# who-am-i [56] (1) Recommended
class ReqWhoAmI(Request):
    def __init__(self, c):
        self.register(c)
        c.send_string("%d 56\n" % (self.id))
        
    def parse_response(self):
        # --> Session-No
        return self.c.parse_int()

# set-user-area [57] (2) Recommended
class ReqSetUserArea(Request):
    def __init__(self, c, person_no, user_area):
        self.register(c)
        c.send_string("%d 57 %d %d\n" % (self.id, person_no, user_area))

# get-last-text [58] (3) Recommended
# FIXME!

# create-anonymous-text-old [59] (3) Obsolete (10)
#                                    Use create-anonymous-text (87)

# find-next-text-no [60] (3) Recommended
class ReqFindNextTextNo(Request):
    def __init__(self, c, start):
        self.register(c)
        c.send_string("%d 60 %d\n" % (self.id, start))
        
    def parse_response(self):
        # --> Text-No
        return self.c.parse_int()

# find-previous-text-no [61] (3) Recommended
class ReqFindPreviousTextNo(Request):
    def __init__(self, c, start):
        self.register(c)
        c.send_string("%d 61 %d\n" % (self.id, start))
        
    def parse_response(self):
        # --> Text-No
        return self.c.parse_int()

# login [62] (4) Recommended
class ReqLogin(Request):
    def __init__(self, c, person_no, password, invisible = 1):
        self.register(c)
        c.send_string("%d 62 %d %dH%s %d\n" %
                      (self.id, person_no, len(password), password, invisible))

# who-is-on-ident [63] (4) Obsolete (9) Use who-is-on-dynamic (83) and
#                                           get-static-session-info (84)
# get-session-info-ident [64] (4) Obsolete (9) Use who-is-on-dynamic (83) and
#                                              get-static-session-info (84)
# re-lookup-person [65] (5) Obsolete (7) Use re-z-lookup (74)
# re-lookup-conf [66] (5) Obsolete (7) Use re-z-lookup (74)
# lookup-person [67] (6) Obsolete (7) Use lookup-z-name (76)
# lookup-conf [68] (6) Obsolete (7) Use lookup-z-name (76)

# set-client-version [69] (6) Recommended
class ReqSetClientVersion(Request):
    def __init__(self, c, client_name, client_version):
        self.register(c)
        c.send_string("%d 69 %dH%s %dH%s\n" %
                      (self.id,
                       len(client_name), client_name,
                       len(client_version), client_version))

# get-client-name [70] (6) Recommended
class ReqGetClientName(Request):
    def __init__(self, c, session_no):
        self.register(c)
        c.send_string("%d 70 %d\n" % (self.id, session_no))
        
    def parse_response(self):
        # --> Hollerith
        return self.c.parse_string()

# get-client-version [71] (6) Recommended
class ReqGetClientVersion(Request):
    def __init__(self, c, session_no):
        self.register(c)
        c.send_string("%d 71 %d\n" % (self.id, session_no))
        
    def parse_response(self):
        # --> Hollerith
        return self.c.parse_string()

# mark-text [72] (4) Recommended
class ReqMarkText(Request):
    def __init__(self, c, text_no, mark_type):
        self.register(c)
        c.send_string("%d 72 %d %d\n" % (self.id, text_no, mark_type))

# unmark-text [73] (6) Recommended
class ReqUnmarkText(Request):
    def __init__(self, c, text_no):
        self.register(c)
        c.send_string("%d 73 %d\n" % (self.id, text_no))

# re-z-lookup [74] (7) Recommended
class ReqReZLookup(Request):
    def __init__(self, c, regexp, want_pers = 0, want_confs = 0):
        self.register(c)
        c.send_string("%d 74 %dH%s %d %d\n" %
                      (self.id, len(regexp), regexp, want_pers, want_confs))

    def parse_response(self):
        # --> ARRAY ConfZInfo
        return self.c.parse_array(ConfZInfo)

# get-version-info [75] (7) Recommended
class ReqGetVersionInfo(Request):
    def __init__(self, c):
        self.register(c)
        c.send_string("%d 75\n" % (self.id))

    def parse_response(self):
        # --> Version-Info
        return self.c.parse_object(VersionInfo)

# lookup-z-name [76] (7) Recommended
class ReqLookupZName(Request):
    def __init__(self, c, name, want_pers = 0, want_confs = 0):
        self.register(c)
        c.send_string("%d 76 %dH%s %d %d\n" %
                      (self.id, len(name), name, want_pers, want_confs))

    def parse_response(self):
        # --> ARRAY ConfZInfo
        return self.c.parse_array(ConfZInfo)

# set-last-read [77] (8) Recommended
class ReqSetLastRead(Request):
    def __init__(self, c, conf_no, last_read):
        self.register(c)
        c.send_string("%d 77 %d %d\n" % \
                      (self.id, conf_no, last_read))

# get-uconf-stat [78] (8) Recommended
class ReqGetUconfStat(Request):
    def __init__(self, c, conf_no):
        self.register(c)
        c.send_string("%d 78 %d\n" % (self.id, conf_no))

    def parse_response(self):
        # --> UConference
        return self.c.parse_object(UConference)

# set-info [79] (9) Recommended
# FIXME!

# accept-async [80] (9) Recommended
class ReqAcceptAsync(Request):
    def __init__(self, c, request_list):
        self.register(c)
        c.send_string("%d 80 %s\n" %
                      (self.id,
                       c.array_of_int_to_string(request_list)))

# query-async [81] (9) Recommended
class ReqQueryAsync(Request):
    def __init__(self, c):
        self.register(c)
        c.send_string("%d 81\n" % (self.id))

    def parse_response(self):
        # --> ARRAY INT32
        return self.c.parse_array_of_int()

# user-active [82] (9) Recommended
class ReqUserActive(Request):
    def __init__(self, c):
        self.register(c)
        c.send_string("%d 82\n" % (self.id))

# who-is-on-dynamic [83] (9) Recommended
class ReqWhoIsOnDynamic(Request):
    def __init__(self, c,
                 want_visible = 1, want_invisible = 0,
                 active_last = 0):
        self.register(c)
        c.send_string("%d 83 %d %d %d\n" % \
                      (self.id, want_visible, want_invisible, active_last))

    def parse_response(self):
        # --> ARRAY Dynamic-Session-Info
        return self.c.parse_array(DynamicSessionInfo)

# get-static-session-info [84] (9) Recommended
class ReqGetStaticSessionInfo(Request):
    def __init__(self, c, session_no):
        self.register(c)
        c.send_string("%d 84 %d\n" % (self.id, session_no))

    def parse_response(self):
        # --> Static-Session-Info
        return self.c.parse_object(StaticSessionInfo)

# get-collate-table [85] (10) Recommended
class ReqGetCollateTable(Request):
    def __init__(self, c):
        self.register(c)
        c.send_string("%d 85\n" % (self.id))

    def parse_response(self):
        # --> HOLLERITH
        return self.c.parse_string()

# create-text [86] (10) Recommended
class ReqCreateText(Request):
    def __init__(self, c, text, misc_info, aux_items = []):
        self.register(c)
        raw_misc_info = misc_info.to_string()
        # FIXME: Ignoring aux-items for a while
        c.send_string("%d 86 %dH%s %s 0 { }\n" %
                      (self.id, len(text), text, raw_misc_info))
        
    def parse_response(self):
        # --> Text-No
        return self.c.parse_int()

# create-anonymous-text [87] (10) Recommended
class ReqCreateAnonymousText(Request):
    def __init__(self, c, text, misc_info, aux_items = []):
        self.register(c)
        raw_misc_info = misc_info.to_string()
        # FIXME: Ignoring aux-items for a while
        c.send_string("%d 87 %dH%s %s 0 { }\n" %
                      (self.id, len(text), text, raw_misc_info))
        
    def parse_response(self):
        # --> Text-No
        return self.c.parse_int()

# create-conf [88] (10) Recommended
class ReqCreateConf(Request):
    def __init__(self, c, name, type, aux_items = []):
        self.register(c)
        # FIXME: Ignoring aux-items for a while
        c.send_string("%d 88 %dH%s %s 0 { }\n" %
                      (self.id, len(name), name,
                       type.to_string()))
        
    def parse_response(self):
        # --> Conf-No
        return self.c.parse_int()

# create-person [89] (10) Recommended
class ReqCreatePerson(Request):
    def __init__(self, c, name, passwd, flags, aux_items = []):
        self.register(c)
        # FIXME: Ignoring aux-items for a while
        c.send_string("%d 89 %dH%s %dH%s %s 0 { }\n" %
                      (self.id,
                       len(name), name,
                       len(passwd), passwd,
                       flags.to_string()))
        
    def parse_response(self):
        # --> Pers-No
        return self.c.parse_int()

# get-text-stat [90] (10) Recommended
class ReqGetTextStat(Request):
    def __init__(self, c, text_no):
        self.register(c)
        c.send_string("%d 90 %d\n" %
                      (self.id, text_no))

    def parse_response(self):
        # --> TextStat
        return self.c.parse_object(TextStat)

# get-conf-stat [91] (10) Recommended
class ReqGetConfStat(Request):
    def __init__(self, c, conf_no):
        self.register(c)
        c.send_string("%d 91 %d\n" % (self.id, conf_no))

    def parse_response(self):
        # --> Conference
        return self.c.parse_object(Conference)

# modify-text-info [92] (10) Recommended
# FIXME!
# modify-conf-info [93] (10) Recommended
# FIXME!

# get-info [94] (10) Recommended
class ReqGetInfo(Request):
    def __init__(self, c):
        self.register(c)
        c.send_string("%d 94\n" % (self.id))

    def parse_response(self):
        # --> Info
        return self.c.parse_object(Info)

# modify-system-info [95] (10) Recommended
# FIXME!

# query-predefined-aux-items [96] (10) Recommended
class ReqQueryPredefinedAuxItems(Request):
    def __init__(self, c):
        self.register(c)
        c.send_string("%d 96\n" % (self.id))

    def parse_response(self):
        # --> ARRAY INT32
        return self.c.parse_array_of_int()

# set-expire [97] (10) Experimental
class ReqSetExpire(Request):
    def __init__(self, c, conf_no, expire):
        self.register(c)
        c.send_string("%d 97 %d %d\n" % (self.id, conf_no, expire))

# query-read-texts [98] (10) Recommended
class ReqQueryReadTexts(Request):
    def __init__(self, c, person_no, conf_no):
        self.register(c)
        c.send_string("%d 98 %d %d\n" % (self.id, person_no, conf_no))

    def parse_response(self):
        # --> Membership
        return self.c.parse_object(Membership)


# get-membership [99] (10) Recommended
class ReqGetMembership(Request):
    def __init__(self, c, person_no, first, no_of_confs, want_read_texts):
        self.register(c)
        c.send_string("%d 99 %d %d %d %d\n" % \
                      (self.id, person_no,
                       first, no_of_confs, want_read_texts))

    def parse_response(self):
        # --> ARRAY Membership
        # FIXME: Cannot read result when want_read_texts = 0
        return self.c.parse_array(Membership)

# add-member [100] (10) Recommended
class ReqAddMember(Request):
    def __init__(self, c, conf_no, person_no, priority, where, type):
        self.register(c)
        c.send_string("%d 100 %d %d %d %d %s\n" % \
                      (self.id, conf_no, person_no,
                       priority, where, type.to_string()))

# get-members [101] (10) Recommended
class ReqGetMembers(Request):
    def __init__(self, c, conf_no, first, no_of_members):
        self.register(c)
        c.send_string("%d 101 %d %d %d\n" % \
                      (self.id, conf_no, first, no_of_members))

    def parse_response(self):
        # --> ARRAY Member
        return self.c.parse_array(Member)

# set-membership-type [102] (10) Recommended
class ReqSetMembershipType(Request):
    def __init__(self, c, person_no, conf_no, type):
        self.register(c)
        c.send_string("%d 102 %d %d %s\n" % \
                      (self.id, person_no, conf_no, type.to_string()))

# local-to-global [103] (10) Recommended
class ReqLocalToGlobal(Request):
    def __init__(self, c, conf_no, first_local_no, no_of_existing_texts):
        self.register(c)
        c.send_string("%d 103 %d %d %d\n" % \
                      (self.id, conf_no, first_local_no, no_of_existing_texts))

    def parse_response(self):
        # --> Text-Mapping
        return self.c.parse_object(TextMapping)

# map-created-texts [104] (10) Recommended
class ReqMapCreatedTexts(Request):
    def __init__(self, c, author, first_local_no, no_of_existing_texts):
        self.register(c)
        c.send_string("%d 104 %d %d %d\n" % \
                      (self.id, author, first_local_no, no_of_existing_texts))

    def parse_response(self):
        # --> Text-Mapping
        return self.c.parse_object(TextMapping)

# set-keep-commented [105] (10) Experimental
class ReqSetKeepCommented(Request):
    def __init__(self, c, conf_no, keep_commented):
        self.register(c)
        c.send_string("%d 105 %d %d\n" % (self.id, conf_no, keep_commented))

# set-pers-flags [106] (10) Recommended

class ReqSetPersFlags(Request):
    def __init__(self, c, person_no, flags):
        self.register(c)
        c.send_string("%d 106 %d %s\n" % (self.id,
                                        person_no,
                                        flags.to_string()))

#
# Classes for asynchronous messages from the server are all
# subclasses of AsyncMessage.
#

class AsyncMessage:
    pass

# async-new-text-old [0] (1) Obsolete (10) <DEFAULT>
ASYNC_NEW_TEXT_OLD = 0
class AsyncNewTextOld(AsyncMessage):
    def parse(self, c):
        self.text_no = c.parse_int()
        self.text_stat = c.parse_old_object(TextStat)

# async-i-am-off [1] (1) Obsolete
# async-i-am-on-onsolete [2] (1) Obsolete

# async-new-name [5] (1) Recommended <DEFAULT>
ASYNC_NEW_NAME = 5
class AsyncNewName(AsyncMessage):
    def parse(self, c):
        self.conf_no = c.parse_int()
        self.old_name = c.parse_string()
        self.new_name = c.parse_string()

# async-i-am-on [6] Recommended
ASYNC_I_AM_ON = 6
class AsyncIAmOn(AsyncMessage):
    def parse(self, c):
        self.info = c.parse_object(WhoInfo)

# async-sync-db [7] (1) Recommended <DEFAULT>
ASYNC_SYNC_DB = 7
class AsyncSyncDB(AsyncMessage):
    def parse(self, c):
        pass

# async-leave-conf [8] (1) Recommended <DEFAULT>
ASYNC_LEAVE_CONF = 8
class AsyncLeaveConf(AsyncMessage):
    def parse(self, c):
        self.conf_no = c.parse_int()

# async-login [9] (1) Recommended <DEFAULT>
ASYNC_LOGIN = 9
class AsyncLogin(AsyncMessage):
    def parse(self, c):
        self.person_no = c.parse_int()
        self.session_no = c.parse_int()

# async-broadcast [10] Obsolete

# async-rejected-connection [11] (1) Recommended <DEFAULT>
ASYNC_REJECTED_CONNECTION = 11
class AsyncRejectedConnection(AsyncMessage):
    def parse(self, c):
        pass

# async-send-message [12] (1) Recommended <DEFAULT>
ASYNC_SEND_MESSAGE = 12
class AsyncSendMessage(AsyncMessage):
    def parse(self, c):
        self.recipient = c.parse_int()
        self.sender = c.parse_int()
        self.message = c.parse_string()

# async-logout [13] (1) Recommended <DEFAULT>
ASYNC_LOGOUT = 13
class AsyncLogout(AsyncMessage):
    def parse(self, c):
        self.person_no = c.parse_int()
        self.session_no = c.parse_int()

# async-deleted-text [14] (10) Recommended
ASYNC_DELETED_TEXT = 14
class AsyncDeletedText(AsyncMessage):
    def parse(self, c):
        self.text_no = c.parse_int()
        self.text_stat = c.parse_object(TextStat)

# async-new-text [15] (10) Recommended
ASYNC_NEW_TEXT = 15
class AsyncNewText(AsyncMessage):
    def parse(self, c):
        self.text_no = c.parse_int()
        self.text_stat = c.parse_object(TextStat)

# async-new-recipient [16] (10) Recommended
ASYNC_NEW_RECIPIENT = 16
class AsyncNewRecipient(AsyncMessage):
    def parse(self, c):
        self.text_no = c.parse_int()
        self.conf_no = c.parse_int()
        self.type = c.parse_int()

# async-sub-recipient [17] (10) Recommended
ASYNC_SUB_RECIPIENT = 17
class AsyncSubRecipient(AsyncMessage):
    def parse(self, c):
        self.text_no = c.parse_int()
        self.conf_no = c.parse_int()
        self.type = c.parse_int()

# async-new-membership [18] (10) Recommended
ASYNC_NEW_MEMBERSHIP = 18
class AsyncNewMembership(AsyncMessage):
    def parse(self, c):
        self.person_no = c.parse_int()
        self.conf_no = c.parse_int()

async_dict = {
    ASYNC_NEW_TEXT_OLD: AsyncNewTextOld,
    ASYNC_NEW_NAME: AsyncNewName,
    ASYNC_I_AM_ON: AsyncIAmOn,
    ASYNC_SYNC_DB: AsyncSyncDB,
    ASYNC_LEAVE_CONF: AsyncLeaveConf,
    ASYNC_LOGIN: AsyncLogin,
    ASYNC_REJECTED_CONNECTION: AsyncRejectedConnection,
    ASYNC_SEND_MESSAGE: AsyncSendMessage,
    ASYNC_LOGOUT: AsyncLogout,
    ASYNC_DELETED_TEXT: AsyncDeletedText,
    ASYNC_NEW_TEXT: AsyncNewText,
    ASYNC_NEW_RECIPIENT: AsyncNewRecipient,
    ASYNC_SUB_RECIPIENT: AsyncSubRecipient,
    ASYNC_NEW_MEMBERSHIP: AsyncNewMembership
    }

#
# CLASSES for KOM data types
#

# TIME

class Time:
    def __init__(self):
        # FIXME: Do we ever send these to the server?
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

# RESULT FROM LOOKUP-Z-NAME

class ConfZInfo:
    def parse(self, c):
        self.name = c.parse_string()
        self.type = c.parse_old_object(ConfType)
        self.conf_no = c.parse_int()

    def __repr__(self):
        return "<ConfZInfo %d: %s>" % \
            (self.conf_no, self.name)

# RAW MISC-INFO (AS IT IS IN PROTOCOL A)

class RawMiscInfo:
    def parse(self, c):
        self.type = c.parse_int()
        if self.type in [MI_REC_TIME, MI_SENT_AT]:
            self.data = c.parse_object(Time)
        else:
            self.data = c.parse_int()

    def __repr__(self):
        return "<MiscInfo %d: %s>" % (self.type, self.data)

# COOKED MISC-INFO (MORE TASTY)
# N.B: This class represents the whole array, not just one item

class MIRecipient:
    def __init__(self, type = MIR_TO, recpt = 0):
        self.type = type
        self.recpt = recpt
        self.loc_no = None
        self.rec_time = None
        self.sent_by = None
        self.sent_at = None

    def decode_additional(self, raw, i):
        while i < len(raw):
            if raw[i].type == MI_LOC_NO:
                self.loc_no = raw[i].data
            elif raw[i].type == MI_REC_TIME:
                self.rec_time = raw[i].data
            elif raw[i].type == MI_SENT_BY:
                self.sent_by = raw[i].data
            elif raw[i].type == MI_SENT_AT:
                self.sent_at = raw[i].data
            else:
                return i 
            i = i + 1
        return i

    def get_tuples(self):
        return [(self.type, self.recpt)]

class MICommentTo:
    def __init__(self, type = MIC_COMMENT, text_no = 0):
        self.type = type
        self.text_no = text_no
        self.sent_by = None
        self.sent_at = None
        
    def decode_additional(self, raw, i):
        while i < len(raw):
            if raw[i].type == MI_SENT_BY:
                self.sent_by = raw[i].data
            elif raw[i].type == MI_SENT_AT:
                self.sent_at = raw[i].data
            else:
                return i 
            i = i + 1
        return i

    def get_tuples(self):
        return [(self.type, self.text_no)]

class MICommentIn:
    def __init__(self, type = MIC_COMMENT, text_no = 0):
        self.type = type
        self.text_no = text_no

    def get_tuples(self):
        return [(self.type + 1, self.text_no)]

class CookedMiscInfo:
    def __init__(self):
        self.recipient_list = []
        self.comment_to_list = []
        self.comment_in_list = []

    def parse(self, c):
        raw = c.parse_array(RawMiscInfo)
        i = 0
        while i < len(raw):
            if raw[i].type in [MI_RECPT, MI_CC_RECPT, MI_BCC_RECPT]:
                r = MIRecipient(raw[i].type, raw[i].data)
                i = r.decode_additional(raw, i+1)
                self.recipient_list.append(r)
            elif raw[i].type in [MI_COMM_TO, MI_FOOTN_TO]:
                ct = MICommentTo(raw[i].type, raw[i].data)
                i = ct.decode_additional(raw, i+1)
                self.comment_to_list.append(ct)
            elif raw[i].type in [MI_COMM_IN, MI_FOOTN_IN]:
                ci = MICommentIn(raw[i].type, raw[i].data - 1 ) # KLUDGE :-)
                i = i + 1
                self.comment_in_list.append(ci)
            else:
                raise ProtocolError

    def to_string(self):
        list = []
        for r in self.recipient_list + \
            self.comment_to_list + \
            self.comment_in_list:
            list = list + r.get_tuples()
        return "%d { %s}" % (len(list),
                             string.join(map(lambda x: "%d %d " % \
                                             (x[0], x[1]), list), ""))
                             

# AUX INFO

class AuxItemFlags:
    def __init__(self):
        self.deleted = 0
        self.inherit = 0
        self.secret = 0
        self.hide_creator = 0
        self.dont_garb = 0
        self.reserved2 = 0
        self.reserved3 = 0
        self.reserved4 = 0

    def parse(self, c):
        (self.deleted,
         self.inherit,
         self.secret,
         self.hide_creator,
         self.dont_garb,
         self.reserved2,
         self.reserved3,
         self.reserved4) = c.parse_bitstring(8)

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
        self.created_at = c.parse_object(Time)
        self.flags = c.parse_object(AuxItemFlags)
        self.inherit_limit = c.parse_int()
        self.data = c.parse_string()
     
# TEXT

class TextStat:
    def __init__(self):
        self.creation_time = None
        self.author = None
        self.no_of_lines = None
        self.no_of_chars = None
        self.no_of_marks = None
        self.misc_info = [] # FIXME: Better representation!
        self.aux_items = []

    def parse(self, c, old_format = 0):
        self.creation_time = c.parse_object(Time)
        self.author = c.parse_int()
        self.no_of_lines = c.parse_int()
        self.no_of_chars = c.parse_int()
        self.no_of_marks = c.parse_int()
        self.misc_info = c.parse_object(CookedMiscInfo)
        if old_format:
            self.aux_items = []
        else:
            self.aux_items = c.parse_array(AuxItem)

# CONFERENCE

class ConfType:
    def __init__(self):
        self.rd_prot = 0
        self.original = 0
        self.secret = 0
        self.letterbox = 0
        self.allow_anonymous = 0
        self.forbid_secret = 0
        self.reserved2 = 0
        self.reserved3 = 0

    def parse(self, c, old_format = 0):
        if old_format:
            (self.rd_prot,
             self.original,
             self.secret,
             self.letterbox) = c.parse_bitstring(4)
            (self.allow_anonymous,
             self.forbid_secret,
             self.reserved2,
             self.reserved3) = (0,0,0,0)
        else:
            (self.rd_prot,
             self.original,
             self.secret,
             self.letterbox,
             self.allow_anonymous,
             self.forbid_secret,
             self.reserved2,
             self.reserved3) = c.parse_bitstring(8)

    def to_string(self):
        return "%d%d%d%d%d%d%d%d" % \
               (self.rd_prot,
                self.original,
                self.secret,
                self.letterbox,
                self.allow_anonymous,
                self.forbid_secret,
                self.reserved2,
                self.reserved3)

class Conference:
    def parse(self, c):
        self.name = c.parse_string()
        self.type = c.parse_object(ConfType)
        self.creation_time = c.parse_object(Time)
        self.last_written = c.parse_object(Time)
        self.creator = c.parse_int()
        self.presentation = c.parse_int()
        self.supervisor = c.parse_int()
        self.permitted_submitters = c.parse_int()
        self.super_conf = c.parse_int()
        self.msg_of_day = c.parse_int()
        self.nice = c.parse_int()
        self.keep_commented = c.parse_int()
        self.no_of_members = c.parse_int()
        self.first_local_no = c.parse_int()
        self.no_of_texts = c.parse_int()
        self.expire = c.parse_int()
        self.aux_items = c.parse_array(AuxItem)

    def __repr__(self):
        return "<Conference %s>" % self.name
    
class UConference:
    def parse(self, c):
        self.name = c.parse_string()
        self.type = c.parse_object(ConfType)
        self.highest_local_no = c.parse_int()
        self.nice = c.parse_int()

    def __repr__(self):
        return "<UConference %s>" % self.name
    
# PERSON

class PrivBits:
    def __init__(self):
        self.wheel = 0
        self.admin = 0
        self.statistic = 0
        self.create_pers = 0
        self.create_conf = 0
        self.change_name = 0
        self.flg7 = 0
        self.flg8 = 0
        self.flg9 = 0
        self.flg10 = 0
        self.flg11 = 0
        self.flg12 = 0
        self.flg13 = 0
        self.flg14 = 0
        self.flg15 = 0
        self.flg16 = 0

    def parse(self, c):
        (self.wheel,
         self.admin,
         self.statistic,
         self.create_pers,
         self.create_conf,
         self.change_name,
         self.flg7,
         self.flg8,
         self.flg9,
         self.flg10,
         self.flg11,
         self.flg12,
         self.flg13,
         self.flg14,
         self.flg15,
         self.flg16) = c.parse_bitstring(16)

    def to_string(self):
        return "%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d" % \
               (self.wheel,
                self.admin,
                self.statistic,
                self.create_pers,
                self.create_conf,
                self.change_name,
                self.flg7,
                self.flg8,
                self.flg9,
                self.flg10,
                self.flg11,
                self.flg12,
                self.flg13,
                self.flg14,
                self.flg15,
                self.flg16)
    
class PersonalFlags:
    def __init__(self):
        self.unread_is_secret = 0
        self.flg2 = 0
        self.flg3 = 0
        self.flg4 = 0
        self.flg5 = 0
        self.flg6 = 0
        self.flg7 = 0
        self.flg8 = 0

    def parse(self, c):
        (self.unread_is_secret,
         self.flg2,
         self.flg3,
         self.flg4,
         self.flg5,
         self.flg6,
         self.flg7,
         self.flg8) = c.parse_bitstring(8)

    def to_string(self):
        return "%d%d%d%d%d%d%d%d" % \
               (self.unread_is_secret,
                self.flg2,
                self.flg3,
                self.flg4,
                self.flg5,
                self.flg6,
                self.flg7,
                self.flg8)

class Person:
    def parse(self, c):
        self.username = c.parse_string()
        self.privileges = c.parse_object(PrivBits)
        self.flags = c.parse_object(PersonalFlags)
        self.last_login = c.parse_object(Time)
        self.user_area = c.parse_int()
        self.total_time_present = c.parse_int()
        self.sessions = c.parse_int()
        self.created_lines = c.parse_int()
        self.created_bytes = c.parse_int()
        self.read_texts = c.parse_int()
        self.no_of_text_fetches = c.parse_int()
        self.created_persons = c.parse_int()
        self.created_confs = c.parse_int()
        self.first_created_local_no = c.parse_int()
        self.no_of_created_texts = c.parse_int()
        self.no_of_marks = c.parse_int()
        self.no_of_confs = c.parse_int()

# MEMBERSHIP

class MembershipType:
    def __init__(self):
        self.invitation = 0
        self.passive = 0
        self.secret = 0
        self.reserved1 = 0
        self.reserved2 = 0
        self.reserved3 = 0
        self.reserved4 = 0
        self.reserved5 = 0

    def parse(self, c):
        (self.invitation,
         self.passive,
         self.secret,
         self.reserved1,
         self.reserved2,
         self.reserved3,
         self.reserved4,
         self.reserved5) = c.parse_bitstring(8)

    def to_string(self):
        return "%d%d%d%d%d%d%d%d" % \
               (self.invitation,
                self.passive,
                self.secret,
                self.reserved1,
                self.reserved2,
                self.reserved3,
                self.reserved4,
                self.reserved5)

class Membership:
    def parse(self, c):
        self.position = c.parse_int()
        self.last_time_read  = c.parse_object(Time)
        self.conference = c.parse_int()
        self.priority = c.parse_int()
        self.last_text_read = c.parse_int()
        self.read_texts = c.parse_array_of_int()
        self.added_by = c.parse_int()
        self.added_at = c.parse_object(Time)
        self.type = c.parse_object(MembershipType)

class Member:
    def parse(self, c):
        self.member  = c.parse_int()
        self.added_by = c.parse_int()
        self.added_at = c.parse_object(Time)
        self.type = c.parse_object(MembershipType)

# TEXT MAPPING

class TextNumberPair:
    def parse(self, c):
        self.local_number = c.parse_int()
        self.global_number = c.parse_int()
    
class TextMapping:
    def parse(self, c):
        self.range_begin = c.parse_int()
        self.range_end = c.parse_int()
        self.later_texts_exists = c.parse_int()
        self.block_type = c.parse_int()

        self.dict = {}
        if self.block_type == 0:
            # Sparse
            print "[SPARSE TEXTMAPPING NOT TESTED]"
            self.sparse_list = c.parse_array(TextNumberPair)
            for tnp in self.sparse_list:
                self.dict[tnp.local_number] = tnp.global_number
                
        elif self.block_type == 1:
            # Dense
            self.dense_first = c.parse_int()
            self.dense_texts = c.parse_array_of_int()
            local_number = self.dense_first
            for global_number in self.dense_texts:
                self.dict[local_number] = global_number
                local_number = local_number + 1
        else:
            raise ProtocolError

# MARK

class Mark:
    def parse(self, c):
        self.text_no = c.parse_int()
        self.type = c.parse_int()

    def __repr__(self):
        return "<Mark %d (%d)>" % (self.text_no, self.type)


# SERVER INFORMATION

class Info:
    def __init__(self):
        self.version = None
        self.conf_pres_conf = None
        self.pers_pres_conf = None
        self.motd_conf = None
        self.kom_news_conf = None
        self.motd_of_lyskom = None
        self.aux_item_list = []

    def parse(self, c):
        self.version = c.parse_int()
        self.conf_pres_conf = c.parse_int()
        self.pers_pres_conf = c.parse_int()
        self.motd_conf = c.parse_int()
        self.kom_news_conf = c.parse_int()
        self.motd_of_lyskom = c.parse_int()
        self.aux_item_list = c.parse_array(AuxItem)

class VersionInfo:
    def parse(self, c):
        self.protocol_version = c.parse_int()
        self.server_software = c.parse_string()
        self.software_version = c.parse_string()

    def __repr__(self):
        return "<VersionInfo protocol %d by %s %s>" % \
               (self.protocol_version,
                self.server_software, self.software_version)

# SESSION INFORMATION

class SessionFlags:
    def parse(self, c):
        (self.invisible,
         self.user_active_used,
         self.user_absent,
         self.reserved3,
         self.reserved4,
         self.reserved5,
         self.reserved6,
         self.reserved7) = c.parse_bitstring(8)

class DynamicSessionInfo:
    def parse(self, c):
        self.session = c.parse_int()
        self.person = c.parse_int()
        self.working_conference = c.parse_int()
        self.idle_time = c.parse_int()
        self.flags = c.parse_object(SessionFlags)
        self.what_am_i_doing  = c.parse_string()

class StaticSessionInfo:
    def parse(self, c):
        self.username = c.parse_string()
        self.hostname = c.parse_string()
        self.ident_user = c.parse_string()
        self.connection_time = c.parse_object(Time)
     
class WhoInfo:
    def parse(self, c):
        self.person = c.parse_int()
        self.working_conference = c.parse_int()
        self.session = c.parse_int()
        self.what_am_i_doing  = c.parse_string()
        self.username = c.parse_string()
     
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
        self.async_handlers = {}
        
        # Send initial string 
        self.send_string("A%dH%s\n" % (len(user), user))

        # Wait for answer "LysKOM\n"
        resp = self.receive_string(7) # FIXME: receive line here
        if resp <> "LysKOM\n":
            raise BadInitialResponse

    # ASYNCHRONOUS MESSAGES HANDLERS
    
    def add_async_handler(self, msg_no, handler):
        if not async_dict.has_key(msg_no):
            raise UnimplementedAsync
        if self.async_handlers.has_key(msg_no):
            self.async_handlers[msg_no].append(handler)
        else:
            self.async_handlers[msg_no] = [handler]

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

        if async_dict.has_key(msg_no):
            msg = async_dict[msg_no]()
            msg.parse(self)
            if self.async_handlers.has_key(msg_no):
                for handler in self.async_handlers[msg_no]:
                    handler(msg,self)
        else:
            raise UnimplementedAsync, msg_no
        
    # PARSING KOM DATA TYPES

    def parse_object(self, classname):
        obj = classname()
        obj.parse(self)
        return obj
        
    def parse_old_object(self, classname):
        obj = classname()
        obj.parse(self, old_format=1)
        return obj
        
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

    def parse_array_of_int(self):
        len = self.parse_int()
        res = []
        if len > 0:
            left = self.parse_first_non_ws()
            if left <> "{": raise ProtocolError
            for i in range(0, len):
                res.append(self.parse_int())
            right = self.parse_first_non_ws()
            if right <> "}": raise ProtocolError
        else:
            star = self.parse_first_non_ws()
            if star <> "*": raise ProtocolError
        return res

    def array_of_int_to_string(self, array):
        return "%d { %s }" % (len(array),
                             string.join(map(str, array), " "))
                             
    # PARSING BITSTRINGS
    def parse_bitstring(self, len):
        res = []
        char = self.parse_first_non_ws()
        for i in range(0,len):
            if char == "0":
                res.append(0)
            elif char == "1":
                res.append(1)
            else:
                raise ProtocolError
            char = self.receive_char()
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
# CLASS for a cached connection
#
# Caches for:
# - UConference
# - Conference
# - Person
# - TextStat 
#
# No negative caching. No time-outs.
# Some automatic invalidation (if accept-async has been called appropriately).

class CachedConnection(Connection):
    def __init__(self, host, port = 4894, user = ""):
        Connection.__init__(self, host, port, user)

        self.uconferences = Cache(self.fetch_uconference)
        self.conferences = Cache(self.fetch_conference)
        self.persons = Cache(self.fetch_person)
        self.textstats = Cache(self.fetch_textstat)

        self.add_async_handler(ASYNC_NEW_NAME, self.cah_conference)
        self.add_async_handler(ASYNC_LEAVE_CONF, self.cah_conference)
        self.add_async_handler(ASYNC_DELETED_TEXT, self.cah_textstat)
        self.add_async_handler(ASYNC_NEW_RECIPIENT, self.cah_textstat)
        self.add_async_handler(ASYNC_SUB_RECIPIENT, self.cah_textstat)
        self.add_async_handler(ASYNC_DELETED_TEXT, self.cah_textstat)

    # Fetching functions (internal use)
    def fetch_uconference(self, no):
        return ReqGetUconfStat(self, no).response()

    def fetch_conference(self, no):
        return ReqGetConfStat(self, no).response()

    def fetch_person(self, no):
        return ReqGetPersonStat(self, no).response()

    def fetch_textstat(self, no):
        return ReqGetTextStat(self, no).response()

    # Handlers for asynchronous messages (internal use)
    # (used to invalidate cache entries)

    def cah_conference(self, msg, c):
        self.conferences.invalidate(msg.conf_no)
        self.uconferences.invalidate(msg.conf_no)

    def cah_textstat(self, msg, c):
        self.textstats.invalidate(msg.text_no)

    # Common operation: get name of conference (via uconference)
    def conf_name(self, conf_no, default = ""):
        try:
            return self.uconferences[conf_no].name
        except:
            pass

        return default

# Cache class for use internally by CachedConnection
class Cache:
    def __init__(self, fetcher):
        self.dict = {}
        self.fetcher = fetcher
        
    def __getitem__(self, no):
        if self.dict.has_key(no):
            return self.dict[no]
        self.dict[no] = self.fetcher(no)
        return self.dict[no]

    def invalidate(self, no):
        if self.dict.has_key(no):
            del self.dict[no]
            
        
        
