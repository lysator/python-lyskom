#!/usr/bin/python
# Virtual classes to walk a conference, e.g. for statistics gathering
# $Id: komconfwalker.py,v 1.3 2001/03/05 22:03:14 kent Exp $
# (C) 2000, 2001 Kent Engström. Released under GPL.

import sys
import time

import kom

# Needs jddate from the lyspython collection
import jddate

#
# DATE PERIOD CLASS 
#
# This class is used to keep track of an open, closed or half-open
# date interval, and to figure out where a date is in relation to
# the interval.
#

class Period:
    def __init__(self):
        # Unlimited to start with
        self.begin = None
        self.end = None

    def __repr__(self):
        return "<Period %s ... %s>" % (self.begin, self.end)
    
    def set_today(self):
        self.begin = self.end = jddate.FromToday()

    def set_yesterday(self):
        self.begin = self.end = jddate.FromToday() -1

    def set_this_week(self):
        today = jddate.FromToday()
        self.begin = today.GetWeekStart()
        self.end = today.GetWeekEnd()

    def set_last_week(self):
        today = jddate.FromToday()
        self.begin = today.GetWeekStart() - 7
        self.end = today.GetWeekEnd() - 7 

    def set_this_month(self):
        today = jddate.FromToday()
        self.begin = today.GetMonthStart()
        self.end = today.GetMonthEnd()

    def set_last_month(self):
        today = jddate.FromToday()
        self.begin = (today.GetMonthStart()-1).GetMonthStart()
        self.end = self.begin.GetMonthEnd()

    def set_begin(self, str):
        self.begin = jddate.FromString(str)

    def set_end(self, str):
        self.end = jddate.FromString(str)

    def ymd_compare(self, y, m, d):
        # Return -1 if the date is before our beginning,
        #         0 if the date is within our limits (inclusively), or
        #        +1 if the date is after our end.
        date = jddate.FromYMD(y, m, d)
        if self.begin is not None and date < self.begin: return -1
        if self.end is not None and date > self.end: return +1
        return 0
    
    def ymd_is_inside(self, y, m, d):
        # Return true iff the date is within our boundaries (inclusively)
        return self.ymd_compare(y, m, d) == 0

    def format(self):
        if self.begin is None and self.end is None:
            return "obegränsad"
        elif self.begin is None:
            return "till och med " + self.end.GetString_YYYY_MM_DD()
        elif self.end is None:
            return "från och med " + self.begin.GetString_YYYY_MM_DD()
        else:
            return self.begin.GetString_YYYY_MM_DD() + " ... " +\
                   self.end.GetString_YYYY_MM_DD()
            
#
# CONFTEMPORALWALKER CLASS
#
# Walk a conference (as a certain person) in date/time order
# The period argument determines which articles should be processed,
# and the mark_earlier and mark_processed arguments which articles
# should be marked as read (articles after the period are never marked).
#

class ConfTemporalWalker:
    def __init__(self, conn, person, conference, period,
                 mark_earlier = 0, mark_processed = 0,
                 debug = 0):
        self.conn = conn
        self.person = person
        self.conference = conference
        self.period = period
        self.mark_earlier = mark_earlier
        self.mark_processed = mark_processed
        self.debug = debug

        self.no_of_articles = 0
        self.first_created = None
        self.last_created = None

    def walk(self):
        # Traverse the texts.
        unread_texts = self.conn.get_unread_texts(self.person, self.conference)
        if self.debug:
            sys.stderr.write("Number of unread texts: %d\n" %len(unread_texts))

        for (loc_no, global_no) in unread_texts:
            # Skip erased texts.
            # FIXME: Some day, somebody should figure out if entries
            # with global_no == 0 should really be present in the
            # list given to us by kom.py.
            if global_no == 0:
                continue
            ts = self.conn.textstats[global_no]

            # Check creation time of article
            created = ts.creation_time.to_python_time()
            cmp = self.period.ymd_compare(ts.creation_time.year + 1900,
                                          ts.creation_time.month + 1,
                                          ts.creation_time.day)
            if cmp < 0:
                # Earlier than the requested period
                if self.debug:
                    sys.stderr.write("- %d %s\n" %( global_no, time.ctime(created)))
                if self.mark_earlier:
                    kom.ReqMarkAsRead(self.conn,
                                      self.conference,
                                          [loc_no]).response()

            elif cmp > 0:
                # Later then the requested period
                if self.debug:
                    sys.stderr.write("+ %d %s\n" %( global_no, time.ctime(created)))
            else:
                # Inside the requested period
                if self.debug:
                    sys.stderr.write("* %d %s\n" %( global_no, time.ctime(created)))
                self.internal_process(loc_no, global_no, ts, created)

                if self.mark_processed:
                    kom.ReqMarkAsRead(self.conn, self.conference, [loc_no]).response()
            

    def internal_process(self, loc_no, global_no, ts, created):
        self.no_of_articles = self.no_of_articles + 1
        if self.first_created is None:
            self.first_created = created
        self.last_created = created
        self.process(loc_no, global_no, ts)

    def process(self, loc_no, global_no, ts):
        # Override this method to define how articles are to be processed
        pass
    
        
