# Tabulator and Histogram classes refactored out from the
# python-lyskom program komconfstats.
# $Id: tabulator.py,v 1.4 2002/01/27 21:35:05 kent Exp $
# (C) 2000-2002 Kent Engström. Released under GPL.
#

import string
import math

# Handle counts and nouns
def get_count_with_noun(count, singularis, pluralis = None):
    if pluralis is None or count == 1:
        return "%d %s" % (count, singularis)
    else:
        return "%d %s" % (count, pluralis)

# Handle double counts and nouns
def get_counts_with_noun(count, total_count, singularis, pluralis = None):
    if pluralis is None or (count <= 1 and total_count == 1):
        return "%d/%d %s" % (count, total_count, singularis)
    else:
        return "%d/%d %s" % (count, total_count, pluralis)


# The comments below were written when the classes were part of
# the python-lyskom program komconstats. Please check out that
# that program to get a hint on how to use the classses.


#
# Main classes for recording information, and their specializations.
#
# Tabulator is the most central class of them all. For a simple report
# such as "Articles per author", there is a single Tabulator (of
# subclass ConfNameTabulator) to handle the report. In its dictionary,
# each author gets an Entry that counts the texts written by him or her.
#
# For a two-dimensional report such as "Articles per subject line and
# author", the top-level Tabulator has a dictionary where each subject
# line gets a Tabulator (a ConfNameTabulator to be precise) of its
# own. Each such Tabulator has its own dictionary where the different
# authors using that subject lines get their Entries stored.
#
# The normal Tabulator class and its specializations produce reports
# sorted on the count (in descending order). The Histogram class and
# its specializations instead sort on the key, include lines where
# count is zero and show a bar of stars to visualize the count.
#
# New subclasses of Tabulator and Histogram should only be derived to
# handle large changes such as different key formats (or totally new
# forms of tabulation). Smaller customizations, such as titles,
# information on what kind of things that are counted, limits on the
# size of a report, etc., should be handled by the TabulatorProperties
# class. For each report, there is a chain of TabulatorProperties objects
# (just like a single-linked list in C or Pascal) with one object 
# for each level of the report.
#
# Now, read the code, and join me again when its time to review the
# Report class.

class Entry:
    def __init__(self, key, properties_ignored = None):
        self.key = key
        self.count = 0 # The normal, successful things we really count
        self.total_count = 0 # Everything, for use in relative reports
        
    def tabulate(self, sub_keys, normal=1, total=1):
        self.count = self.count + normal
        self.total_count = self.total_count + total

    def is_empty(self):
        return self.count == 0

    def report(self, indent, levels, relative):
        # This is kind of faked, but it makes the code simpler...
        return []
       
class Tabulator(Entry):
    def __init__(self, key = None, properties = None):
        Entry.__init__(self, key)
        self.dict = {}  # Contains Entries/Tabulators
        if properties is None:
            self.prop = TabulatorProperties(self.__class__)
        else:
            self.prop = properties
            
    def tabulate(self, keys, normal=1, total=1):
        Entry.tabulate(self, keys, normal, total)

        if keys == []: return
        key = self.data_to_key(keys[0])
            
        if not self.dict.has_key(key):
            if self.prop.next is None:
                SubClass = Entry
            else:
                SubClass = self.prop.next.subclass
            self.dict[key] = SubClass(key, self.prop.next)
        self.dict[key].tabulate(keys[1:], normal, total)

    def report(self, indent = 0, levels = None, relative = 0):
        # This method is common for both normal tabulators and histograms

        # No report if we are past the max level
        if levels is not None and indent >= levels: return []
        
        l = [] # Collect lines of text using this one

        if indent == 0:
            # Only the top level should have a title
            if relative:
                countstr = self.prop.get_counts_with_noun(self.count,
                                                          self.total_count)
            else:
                countstr = self.prop.get_count_with_noun(self.count)
                
            l.append("%s (%s)" % (self.get_title(levels, relative),
                                  countstr))
            l.append("")
            self.report_extra_header(l)

        # Now, do the real work. Notice how "l" will be modified by
        # the addition of the report body lines.

        self.report_body(l, indent, levels, relative)

        return l

    def get_title(self, levels = None, relative = 0):
        return self.prop.get_title(levels, relative)

    def report_body(self, l, indent, levels, relative):
        # Specific for tabulators, overridden by histograms
        
        istr = "      " * indent # Six spaces for each level of indentation

        if relative:
            # A relative report should be order by percentage
            # As we make it an integer, we can get ties.
            sortlist = map(lambda x, d=self.dict: \
                           (int(-100*float(d[x].count)/d[x].total_count), d[x]),
                           self.dict.keys())
        else:
            # An absolute report is ordered by the count itself
            sortlist = map(lambda x, d=self.dict: (-d[x].count, d[x]),
                           self.dict.keys())
        sortlist.sort()
        pos = 1
        last_occ = None 
        bailed_out = 0 # This will be set if we break because of max_displayed
        for (occ, entry) in sortlist:
            # An entry with count == 0 may be present if total_count > 0
            # Skip it!
            if entry.count == 0: continue
            
            occ = - occ # or percentage in relative version
            key = self.key_to_display(entry.key)

            if self.prop.max_displayed is not None and \
               pos > self.prop.max_displayed:
                bailed_out = 1
                break

            if occ <> last_occ:
                pos_str = str(pos)
            else:
                pos_str = '"'
            if relative:
                l.append("%s%3s) %s (%d%%, %d/%d)" % (istr,
                                                         pos_str,
                                                         key,
                                                         occ,
                                                         entry.count,
                                                         entry.total_count,
                                                         ))
            else:
                l.append("%s%3s) %s (%d)" % (istr, pos_str, key, occ))
            l.extend(entry.report(indent = indent + 1,
                                  levels = levels,
                                  relative = relative))
            pos = pos + 1
            last_occ = occ

        if bailed_out:
            l.append("%s     /%s/" % \
                     (istr,
                      get_count_with_noun(len(sortlist) -
                                          self.prop.max_displayed,
                                          "utelämnad rad","utelämnade rader")
                      ))
                               
        l.append("")
        
    # Override these methods if needed

    def report_extra_header(self, l):
        return

    def data_to_key(self, data):
        # This is how the data sent in will be transformed before
        # being used as a key.
        return data

    def key_to_display(self, key):
        # This is how the stored key will be transformed before
        # being displayed.
        return key



class Histogram(Tabulator):
    def report_body(self, l, indent, levels, relative):
        # Specific for histogram, overrides method in Tabulator

        assert not relative # FIXME What should a relative histogram look like?
        
        istr = "      " * indent # Six spaces for each level of indentation

        max_len = 50

        # Find minimum and maximum key, as well as maximum count
        # and maxmimum size of a cooked key

        min_key = None
        max_key = None
        max_occ = 0
        max_key_size = 0
        for (key,entry) in self.dict.items():
            occ = entry.count
            
            if min_key is None:
                min_key = key
            else:
                min_key = min(min_key, key)

            if max_key is None:
                max_key = key
            else:
                max_key = max(max_key, key)

            max_occ = max(max_occ, occ)
            max_key_size = max(max_key_size, len(self.key_to_display(key)))


        # The properties may override this, but only to extend it
        if self.prop.histogram_begin is not None and \
           self.prop.histogram_begin < min_key:
            min_key = self.prop.histogram_begin

        if self.prop.histogram_end is not None and \
           self.prop.histogram_end > max_key:
            max_key = self.prop.histogram_end

        # If we still have no limits, do not
        # generate anything more
        if min_key is None or max_key is None:
            return
        
        if max_occ == 0:
            divisor = 1
        else:
            divisor = (max_occ-1)/max_len+1

        # range(min_key, max_key+1) is not used, as this requires that the
        # type used as key has an __int__ method.
        raw_key = min_key
        while raw_key <= max_key:
            if self.dict.has_key(raw_key):
                entry = self.dict[raw_key]
                occ = entry.count
            else:
                entry = None
                occ = 0
            key = self.key_to_display(raw_key)
            bar_len = occ / divisor
            if divisor > 1 and occ > 0:
                bar_len = bar_len + 1
            
            if occ == 0 and self.prop.histogram_hide_zero:
                l.append("%s     %-*s:" % (istr, max_key_size, key))
            else:
                l.append("%s     %-*s:%5d %s" % (istr, max_key_size, key, occ, "*" * bar_len))

            if entry is not None:
                l.extend(entry.report(indent = indent + 1,
                                      levels = levels,
                                      relative = relative))

            raw_key = raw_key + 1
            
        l.append("")

    def key_to_display(self, key):
        return str(key)

class LogHistogram(Histogram):
    # Virtual --- use a subclass!
    def __init__(self, key = None, properties = None):
        self.logoflogbase = math.log(self.logbase)
        Histogram.__init__(self, key, properties) 
    
    def key_to_display(self, x):
        return "%6d -" % (self.logbase**x)

    def data_to_key(self, x):
        if x == 0: x = 1
        return int(math.log(x)/self.logoflogbase)


class BinHistogram(Histogram):
    # Virtual --- use a subclass!
    def __init__(self, key = None, properties = None):
        Histogram.__init__(self, key, properties)

    def key_to_display(self, x):
        return self.bins[x][1]

    def data_to_key(self, x):
        index = 0
        slot = index
        for (min, name) in self.bins:
            if x >= min:
                slot = index
            index = index + 1
        return slot
    
class TabulatorProperties:
    def __init__(self, subclass):
        self.next = None
        self.subclass = subclass
        self.title = "Rubrik saknas"
        self.what = "något"
        self.singularis = "st"
        self.pluralis = None
        self.max_displayed = None
        self.histogram_begin = None
        self.histogram_end = None
        self.histogram_hide_zero = 0
        
    def add_sub(self, subclass):
        if self.next is not None:
            raise ValueError, "add_sub called twice"
        self.next = TabulatorProperties(subclass)
        return self.next
    
    def set_histogram_range(self, begin = None, end = None):
        self.histogram_begin = begin
        self.histogram_end =   end
        
    def get_count_with_noun(self, count):
        return get_count_with_noun(count, self.singularis, self.pluralis)

    def get_counts_with_noun(self, count, total_count):
        return get_counts_with_noun(count, total_count,
                                   self.singularis, self.pluralis)

    def get_title(self, levels, relative):
        # We need to collect the "what" field from the chain of
        # TabulatorProperties:
        whatlist = []
        p = self
        while p is not None:
            whatlist.append(p.what)
            p = p.next
        if levels is not None:
            whatlist = whatlist[:levels]

        if relative:
            relstr = "; relativt"
        else:
            relstr = ""

        return self.title + ": " + string.join(whatlist, ", ") + relstr
    

#
# REPORT CLASS
#
# Thanks for tuning in to the comment channel again. I promised to
# explain the purpose of this class above. This class is
# able to encapsulate a Tabulator (or one of its subclasses)
# well enough to fool ConfStats.report(). Ask a real OO junkie
# if you really want to know the name of this pattern :-)
#
# The reason for inventing this class is to be able to use the same
# Tabulator to report more than once, with different levels of
# subtabulation. In that way, the same tabulator can produce
# both the "Articles per author" and "Articles per author, subject
# line" reports (but not the "Articles per subject line" or
# "Articles per subject line, author" reports).
#

class Report:
    def __init__(self, tabulator, levels = None, relative = 0):
        self.tabulator = tabulator
        self.levels = levels
        self.relative = relative

    def is_empty(self):
        return self.tabulator.is_empty()
    
    def report(self):
        return self.tabulator.report(levels = self.levels,
                                     relative = self.relative)

    def get_title(self):
        return self.tabulator.get_title(levels = self.levels,
                                        relative = self.relative)        
        
