# LysKOM Protocol A version 10 client interface for Python
# $Id: komformat.py,v 1.1 1999/10/18 09:12:33 kent Exp $
# (C) 1999 Kent Engström. Released under GPL.

# Format a text for display.
# Intented for use in various programs, e.g. komgraph and kommove

# Things to do better:
# - i18n
# - handle more aux_items
# -- Transform "Kommentar" to "Bilaga" when appropriate

import kom
import string

# Recipient types
recipient_type_dict = {
    kom.MIR_TO: "Mottagare",
    kom.MIR_CC: "Extra kopia",
    kom.MIR_BCC: "För kännedom"
    }

# Comment types
comment_type_dict = {
    kom.MIC_COMMENT: "Kommentar",
    kom.MIC_FOOTNOTE: "Fotnot",
    }


# Class to handle display

class Text:
    # The connection must be an instance of a subclass of CachedConnection
    # Passing text_stat and/or text is optional (but reduces communication)
    def __init__(self, connection, text_no, text_stat = None, text = None):
        self.c = connection
        self.text_no = text_no

        if text_stat is not None:
            self.ts = text_stat
        else:
            self.ts = self.c.textstats[text_no]

        if text is not None:
            self.text = text
        else:
            self.text = kom.ReqGetText(self.c, text_no).response()

        first_newline = string.find(self.text, "\n")
        if first_newline <> -1:
            self.subject = self.text[:first_newline]
            self.body = self.text[first_newline + 1:]
        else:
            self.subject = self.text
            self.body = ""

    # INTERNAL (USE EXTERNAL INTERFACE BELOW)

    def get_aux_item_list(self, ai_list, tag):
        list = []
        for ai in ai_list:
            if ai.tag == tag:
                list.append(ai.data)
        return list
    
    def get_aux_item_data(self, ai_list, tag, default = None):
        for ai in ai_list:
            if ai.tag == tag:
                return ai.data
        return default

    def format_mx_author_and_from(self, mx_author, mx_from):
        if mx_author and mx_from:
            return "%s <%s>" % (mx_author, mx_from)
        elif mx_author:
            return mx_author
        else:
            return "<%s>" % mx_from

    def get_name(self, no):
        try:
            return self.c.uconferences[no].name
        except:
            return "Person %d (finns inte)" % self.ts.author

    def get_author(self):
        mx_author = self.get_aux_item_data(self.ts.aux_items, kom.AI_MX_AUTHOR)
        mx_from = self.get_aux_item_data(self.ts.aux_items, kom.AI_MX_FROM)
        if mx_author is not None or mx_from is not None:
            # Prefer external mx_author/mx_from
            return self.format_mx_author_and_from(mx_author, mx_from)
        else:
            # Normal author
            return self.get_name(self.ts.author)

    def get_date_time(self, t):
        return "%04d-%02d-%02d  %02d:%02d" % \
               (t.year + 1900, t.month, t.day, t.hours, t.minutes)


    def get_date_time_written(self):
        mx_date = self.get_aux_item_data(self.ts.aux_items, kom.AI_MX_DATE)
        if mx_date:
            # Prefer external mx_date
            return mx_date
        else:
            # Normal creation_time
            return self.get_date_time(self.ts.creation_time)

    def add_recipient(self, r, s):
        s.append("%s: %s <%d>"  % \
                 (recipient_type_dict[r.type],
                  self.c.conf_name(r.recpt),
                  r.loc_no))

        if r.sent_at is not None:
            s.append("    Sänt:     %s" % self.get_date_time(r.sent_at))

        if r.sent_by is not None:
            s.append("    Sänt av %s" % self.get_name(r.sent_by))

        if r.rec_time is not None:
            s.append("    Mottaget: %s" % self.get_date_time(r.rec_time))

    def add_comment_in(self, ci, s):
        try:
            ts = self.c.textstats[ci.text_no]
            s.append("%s i text %d av %s"  % \
                     (comment_type_dict[ci.type],
                      ci.text_no,
                      self.get_name(ts.author)))
        except kom.NoSuchText:
            s.append("%s i text %d"  % \
                     (comment_type_dict[ci.type],
                      ci.text_no))

    def add_comment_to(self, ct, s):
        try:
            ts = self.c.textstats[ct.text_no]
            s.append("%s till text %d av %s"  % \
                     (comment_type_dict[ct.type],
                      ct.text_no,
                      self.get_name(ts.author)))
        except kom.NoSuchText:
            s.append("%s till text %d"  % \
                     (comment_type_dict[ct.type],
                      ct.text_no))

        if ct.sent_at is not None:
            s.append("    Sänt:     %s" % self.get_date_time(ct.sent_at))

        if ct.sent_by is not None:
            s.append("    Sänt av %s" % self.get_name(ct.sent_by))

    def add_aux_items_if_present(self, format, tag, s):
        list = self.get_aux_item_list(self.ts.aux_items, tag)
        for data in list:
            s.append(format % data)

    def get_subject(self):
        return self.subject

    def get_body(self, max_body_lines = None):
        if max_body_lines is None:
            return self.body
        else:
            body_lines = string.split(self.body, "\n")
            total_lines = len(body_lines)
            if total_lines < max_body_lines:
                return self.body
            else:
                omitted_lines = total_lines - max_body_lines
                return string.join(body_lines[:max_body_lines] +
                                   ["[... %d]" % omitted_lines], "\n") 


    # EXTERNAL INTERFACE

    def get(self, max_body_lines = None):
        s = []

        # Top line: text_no, date, time, lines, author
        date_time = self.get_date_time_written()
        if self.ts.no_of_lines == 1:
            lines = "rad"
        else:
            lines = "rader"
        s.append("%d %s  /%d %s/ %s" % (self.text_no,
                                        date_time,
                                        self.ts.no_of_lines,
                                        lines,
                                        self.get_author()))

        # Envelope sender, attachment filename
        self.add_aux_items_if_present("Sänt av: %s",
                                      kom.AI_MX_ENVELOPE_SENDER,
                                      s)
        self.add_aux_items_if_present('Bilagans filnamn: "%s"',
                                      kom.AI_MX_MIME_FILE_NAME,
                                      s)
        
        # Imported
        mx_from = self.get_aux_item_data(self.ts.aux_items, kom.AI_MX_FROM)
        mx_author = self.get_aux_item_data(self.ts.aux_items, kom.AI_MX_AUTHOR)
        if mx_from or mx_author:
            s.append("Importerad: %s av %s" % \
                     (self.get_date_time(self.ts.creation_time),
                      self.get_name(self.ts.author)))


        # MX_TO, MX_CC, MX_IN_REPLY_TO
        self.add_aux_items_if_present("Extern mottagare: %s",
                                      kom.AI_MX_TO,
                                      s)
        self.add_aux_items_if_present("Extern kopiemottagare: %s",
                                      kom.AI_MX_CC,
                                      s)
        self.add_aux_items_if_present("Externa svar till: %s",
                                      kom.AI_MX_REPLY_TO,
                                      s)
        
        # Misc-info-based lines follows. Note that we display each category
        # separately while the Emacs Lisp client mixes the headers based on the
        # ordering of the raw misc-info list.

        # Comment-to lines
        for ct in self.ts.misc_info.comment_to_list:
            self.add_comment_to(ct, s)
        
        # Recipient lines
        for recpt in self.ts.misc_info.recipient_list:
            self.add_recipient(recpt, s)

        # Subject line
        s.append("Ärende: %s" % self.get_subject())

        # Line of dashes
        s.append("-" * 60)

        # Body
        s.append(self.get_body(max_body_lines))

        # End line: text_no, author, dashes
        line = ("(%d) /%s/" % (self.text_no, self.get_author()) +
                "-" * 52)[:52]
        s.append(line)

        # Comment-in lines
        for ci in self.ts.misc_info.comment_in_list:
            self.add_comment_in(ci, s)
        
        # Done
        return string.join(s, "\n")
        

