#!/usr/bin/python
# -*- coding: Latin-1 -*-
# topmarkings.py, a program to find the texts with most marks.
# Copyright (C) 2002 Erik Forsberg. Released under the GPL.

# This code should, ideally, use a non-existing Walker-class.

import kom
import komparam
import sys
import getopt

__version__ = "$Revision: 1.6 $"

def calculate(conn, starttext, endtext, toplen):
    forbidden = 0
    totalmarkings = 0
    markedtexts = 0
    firstvalid = sys.maxint
    marks = []
    for i in range(toplen):
        marks.append([-1,0])
    for text in xrange(endtext+1, starttext+1, -1):
        try:
            no_of_marks = conn.textstats[text].no_of_marks
            if text < firstvalid:
                firstvalid = text
            if 0 == no_of_marks:
                continue
            else:
                totalmarkings+=no_of_marks
                markedtexts+=1
        except kom.NoSuchText:
            forbidden+=1
            continue
        for i in range(toplen):
            if no_of_marks > marks[i][1]:
                if i < (toplen-1):
                    for j in range(toplen-1, i, -1):
                        marks[j]=marks[j-1]
                marks[i] = [text, no_of_marks]
                break

    return [marks, forbidden, totalmarkings, markedtexts, firstvalid]

    

# MAIN
# Connect and log in
if '__main__' == __name__:
    param = komparam.Parameters(sys.argv[1:])
    (conn, conn_error) = param.connect_and_login(kom.CachedConnection)
    if conn is None:
        sys.stderr.write("%s: %s\n" % (sys.argv[0], conn_error))
        sys.exit(1)

    firsttext = 0
    lasttextoutfile = None
    lasttext = None
    toplistlength = 10
    verbose = 0
    reportmeeting = None

    options, arguments = getopt.getopt(param.get_arguments(),
                                       "",
                                       ["firsttext=",
                                        "firsttextfile=",
                                        "lasttext=",
                                        "lasttextfile=",
                                        "lasttextoutfile=",
                                        "toplistlength=",
                                        "reportmeeting=",
                                        "verbose"])

    for (opt, optarg) in options:
        if '--firsttext' == opt:
            firsttext = int(optarg)
        elif '--firsttextfile' == opt:
            try:
                
                f = open(optarg, 'r')
                firsttext = int(f.readline())
                f.close()
            except IOError:
                print "Couldn't open %s for reading" % optarg
                sys.exit(1)
        elif '--lasttext' == opt:
            lasttext = int(optarg)
        elif '--lasttextfile' == opt:
            try:
                f = open(optarg, 'r')
                lasttext = int(f.readline())
                f.close()
            except IOError:
                print "Couldn't open %s for reading" % optarg
                sys.exit(1)
        elif '--lasttextoutfile' == opt:
            lasttextoutfile = optarg
        elif '--toplistlength' == opt:
            toplistlength = int(optarg)
        elif '--reportmeeting' == opt:
            reportmeeting = int(optarg)
        elif '--verbose' == opt:
            verbose = 1
        else:
            sys.stderr.write("ERROR: Option %s not handled (internal error)\n"
                             % opt)

    if not lasttext:
        lasttext = kom.ReqFindPreviousTextNo(conn, sys.maxint).response()

    if verbose:
        print "Checking texts %d to %d" % (firsttext, lasttext)

    (marks, forbidden, totalmarkings,
     markedtexts, firstvalid) = calculate(conn,
                                          firsttext,
                                          lasttext,
                                          toplistlength)

    if verbose:
        print marks
        
    if lasttextoutfile:
        f = open(lasttextoutfile, 'w')
        f.write("%d\n" % lasttext)
        f.close()

    if markedtexts:	
        avg = float(totalmarkings)/float(markedtexts)
    else:
	avg = 0
    txt = "Markeringsstatistik från text %d (Postad %s\n" \
          "                    till text %d (Postad %s\n" \
          "\n%d texter i intervallet gick ej att läsa.\n\n" \
          "%d texter i intervallet är markerade med sammanlagt %d markeringar"\
          "\nMedelantalet markeringar för en markerad text är alltså %.2f\n"\
          "\nTopp %d följer:\n\n" \
          % (firstvalid,
             conn.textstats[firstvalid].creation_time.to_date_and_time(),
             lasttext,
             conn.textstats[lasttext].creation_time.to_date_and_time(),
             forbidden,
    	     markedtexts, totalmarkings,
             avg, toplistlength)

    for mark in marks:
        if -1 == mark[0]:
            break
        name = conn.conferences[conn.textstats[mark[0]].author].name
        plural = ""
        if mark[1] > 1:
            plural = "ar"
        txt+="<text %d> av %s med %d markering%s\n" % (mark[0], name,
                                                    mark[1], plural)
        textdata = kom.ReqGetText(conn, mark[0], 0,
                                  conn.textstats[mark[0]].no_of_chars).response()
        subj = textdata.split('\n')[0]
					
	for r in conn.textstats[mark[0]].misc_info.recipient_list:
	    conf = r.get_tuples()[0][1]	
	    txt+=" "*len("<text %d> " % mark[0])+ \
	         "<möte %d: %s>" % (conf, conn.conferences[conf].name)+"\n"
        txt+=" "*len("<text %d> " % mark[0])+subj+"\n"

    if verbose:
        print txt

# kom.ReqAddComment(conn, 234, 235).response()

    if reportmeeting:
        misc_info = kom.CookedMiscInfo()
        misc_info.recipient_list.append(kom.MIRecipient(type=kom.MIR_TO,
                                                        recpt=reportmeeting))

        aux_items = []
        
        for mark in marks:
            if -1 == mark[0]:
                break
            aux_items.append(kom.AuxItem(kom.AI_CROSS_REFERENCE,
                                         "T%d %d markeringar." % (mark[0],
                                                                  mark[1])))
#            misc_info.comment_to_list.append(kom.MICommentIn(mark[0]))
        

        text_no = kom.ReqCreateText(conn, "Markeringsstatistik\n"+txt,
                                    misc_info, aux_items).response()
#        for mark in marks:
#            if -1 == mark[0]:
#                break
#            kom.ReqAddComment(conn, mark[0], text_no).response()
        
        
        
        
        

    

