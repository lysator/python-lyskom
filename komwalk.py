#!/usr/bin/python
# LysKOM Protocol A version 10 client interface for Python
# $Id: komwalk.py,v 1.1 1999/10/15 08:51:54 kent Exp $
# (C) 1999 Kent Engström. Released under GPL.

import kom

# The Class

class Walker:
    # The connection has to be a subclass of CachedConnection
    def __init__(self, connection, root_text_no):
        self.c = connection
        self.root_text_no = root_text_no
        self.visited_text_nos= {}

    def walk(self):
        self.visit(self.root_text_no)

    def visit(self, text_no):
        # Check for nodes we have already visited
        if self.visited_text_nos.has_key(text_no):
            return
        else:
            self.visited_text_nos[text_no] = 1
                
        # See if we can get this node
        try:
            text_stat = self.c.textstats[text_no]
        except:
            text_stat = None

        # Visit the node
        if text_stat is not None:
            will_visit_comments = self.visit_node(text_no, text_stat)

            if will_visit_comments:
                for comment_in in text_stat.misc_info.comment_in_list:
                    will_visit_node = self.visit_edge(text_no, text_stat,
                                                      comment_in)
                    if will_visit_node:
                        self.visit(comment_in.text_no)
        else:
            self.visit_node_bad(text_no)

    # Override this to specify behaviour at a text node.
    # Return 1 if comment links should be followed, 0 if not
    def visit_node(self, text_no, text_stat):
        print "VISITING NODE",text_no
        return 1

    # Override this to specify behaviour at a text node
    # for which we cannot get the text-stat
    def visit_node_bad(self, text_no):
        print "BAD NODE",text_no

    # Override this to specify behaviour for a comment/footnote edge
    # Return 1 if the text
    def visit_edge(self, text_no, text_stat, comment):
        print "VISITING EDGE",text_no, "-->", comment.text_no
        return 1
