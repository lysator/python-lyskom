#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Copyright (c) 2004  Pontus Freyhult <pont_tel@soua.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

# 
# This is not a product yet.
#

#
# Python 2.3 probably required
#

AGENT_PERSON = "Budbäraren"
KOMSERVER = "localhost"
logfile = open("/tmp/canidiusstable.log", 'a')
DEFAULT_PORT = '5222'
DEFAULT_RESOURCE = 'LysKOM'

ignore_users = []

# Client specific aux items

AI_CAN_CONF_MESSAGE = 10300
# AI to set on persons using the service. Data should be a text number containing a
# configuration message.

AI_CAN_THREAD = 10301
# Data should be a thread ID

AI_CAN_FROM = 10302
# Data should be a (unstripped) jabber userid

AI_CAN_TO = 10303
# Data should be a (unstripped) jabber userid


import sys

# Can we get around this somehow?

if hasattr(sys,'setdefaultencoding'):
    sys.setdefaultencoding("latin-1")
else:
    print "Warning: Can't change system default encoding, unsupported operation!"

import socket
import jabber
import kom
import os
import mutex
import threading
import time
import re
import traceback
import encodings
import Queue

homed = os.getenv("HOME")

if not homed:   # No such environment variable
    homed = ""
    
AGENT_PASSWORD = open( homed + "/."+ AGENT_PERSON + "_password" ).readline().strip()

daemon_person = -1  # Will be looked up

VERSION = "0.1 $Id: canidius.py,v 1.10 2004/12/15 07:15:59 _cvs_pont_tel Exp $"


komsendq = Queue.Queue()
komsendq_m = mutex.mutex()

sessdict = {}
sessdict_m = mutex.mutex()

threaddict = {}
threaddict_m = mutex.mutex()

log_m = mutex.mutex()

addrre = re.compile("[^<]*<([^>]*)>")

def log(s):
    lock(log_m)
    if logfile:
        logfile.write("%s %s\n" % (time.ctime(),s))
        logfile.flush()
    unlock(log_m)

def utf8_d(s):
    # Ugly tests for detecting strings that are
    # unicode strings already, how to do it 
    # better?
    if isinstance(s,type(u"")):
        return s
    return encodings.codecs.utf_8_decode(s)[0]

def utf8_e(s):
    return encodings.codecs.utf_8_encode(s)[0]

def l1_d(s):
    # See utf8_d
    if isinstance(s,type(u"")):
        return s
    return encodings.codecs.latin_1_decode(s)[0]

def l1_e(s):
    return encodings.codecs.latin_1_encode(s)[0]

class kommessage:
    def __init__(self,to,msg):
        self.to = to
        self.msg = msg

    def send(self,c):
        # Should be called with mutex acquired for c

        try:
            kom.ReqSendMessage(c, self.to, self.msg ).response()
        except kom.MessageNotSent:
            pass # What to do?
            
class komtext:
    def __init__(self,text,mi,ai,thread=''):
        self.text = text
        self.miscinfo = mi
        self.auxitems = ai
        self.thread = thread
        
    def send(self,c):
        # Should be called with mutex acquired for c
        

        if self.thread:
            def rightthread(ts):
                for p in ts.aux_items:
                    if p.tag == AI_CAN_THREAD and p.data == '%s' % self.thread:
                        return 1

            possible_texts = messages_satisfying( rightthread )

            if possible_texts: # Any texts with this thread?
                possible_texts.reverse() # Take the latest
                
                self.miscinfo.comment_to_list.append(
                    kom.MICommentTo(kom.MIC_COMMENT,possible_texts[0]))

                # Make sure we only have one aux item of this type
                removelist = []
                for p in self.auxitems:
                    if p.tag == AI_CAN_THREAD and p.data == '%s' % self.thread:
                        removelist.append(p)
                for p in removelist:
                    self.auxitems.remove(p)

        kom.ReqCreateText(conn,
                          self.text,
                          self.miscinfo,
                          self.auxitems).response()



    
def lock(m):
    #if threading.currentThread().getName() == 'MainThread':
    #    print "Lock"
    #    traceback.print_stack()
    while not m.testandset():
        time.sleep(0.1)

def unlock(m):
    #if threading.currentThread().getName() == 'MainThread':
    #    print "Unlock"
    #    traceback.print_stack()
    m.unlock()

def parse_configmessage(text, report=0, textno=0):
    # Should probably be in person
    tl = text.split("\n")
    nounderstand = []
    conf = {'aliases':[],
            'ignore':[],
            'ignore_presence':[],
            'sendpresence':[],
            'startup_show':'',
            'startup_status':'',
            'def_recpt_time':'30',
            'config_source':textno}
    
    for p in tl:
        if len(p) and p[0] != '#':
            treated = 0

            for q in ('server','userid','password','alias','resource',
                      'port','skip_resources','ignore','ignore_presence',
                      'sendpresence','startup_show','startup_status', 'messages_only',
                      'divert_incoming_to','def_recpt_time'):
                l = filter(None, p.split())
                if l and l[0].lower() == q:
                    if q == 'alias':                        
                        conf['aliases'].append((l[1],l[2]))
                        treated = 1
                    elif q in ('ignore','ignore_presence','sendpresence'):
                        treated = 1
                        for r in l[1:]:
                            conf[q].append(r)
                    else:
                        conf[q] = l[1]
                        treated = 1

            if not treated:
                nounderstand.append(p)

    if nounderstand and report:
        pass # TODO

    conf['ignored_settings'] = nounderstand
    
    sp = conf.keys()

    if 'server' in sp and 'userid' in sp and 'password' in sp:
        if not 'port' in sp:
            conf['port'] = DEFAULT_PORT
        if not 'resource' in sp:
            conf['resource'] = DEFAULT_RESOURCE
        if not 'skip_resources' in sp:
            conf['skip_resources'] = ''

        if not 'letters_only' in sp:
            conf['letters_only'] = 0

        if not 'messages_only' in sp:
            conf['messages_only'] = 0

        if not conf['sendpresence']:            
            for p in conf['aliases']:
                conf['sendpresence'].append(p[1])
            
            
        return conf

    return 


def messages_satisfying(testfunc):
    baselocal = conn.conferences[daemon_person].first_local_no
    texts_to_search = conn.conferences[daemon_person].no_of_texts
    possible_texts = []

    while texts_to_search:

        search_now = min(255, texts_to_search)

        try:
            textmap = kom.ReqLocalToGlobal(conn,
                                           daemon_person,
                                           baselocal,
                                           search_now).response()
        except kom.ServerError:
            textmap = []
            
        for p in textmap.list:
            globtext = p[1]

            if globtext and testfunc( conn.textstats[globtext] ):
                possible_texts.append(globtext)
                            
        texts_to_search = texts_to_search - search_now


    return possible_texts


    
def configmessage(person_no):
    
    try:
        textno = 0

        for p in conn.conferences[person_no].aux_items:
            if p.tag == AI_CAN_CONF_MESSAGE:
                textno = int( p.data )

        if textno:
        
            text = kom.ReqGetText(conn,
                                  textno,
                                  0, conn.textstats[textno].no_of_chars).response()

            for q in filter( lambda x: x.type == kom.MIC_FOOTNOTE,
                             conn.textstats[textno].misc_info.comment_in_list ):
                text = text +'\n' + kom.ReqGetText(conn,
                                             q.text_no,
                                             0,
                                             conn.textstats[q.text_no].no_of_chars).response()
                            

            config = parse_configmessage(text,textno=textno)

            
            if config:
                return person(person_no,config)
    except kom.ServerError:
        return

def check_active(person_no):
    if person_no in ignore_users:
        return None
    return configmessage(person_no)

class person:
    def __init__(self, person_no,conf):
        self.me = person_no
        self.realme = person_no
        self.mutex = mutex.mutex()
        self.conf = conf
        
        if conf.has_key('divert_incoming_to'):
            self.me = int(conf['divert_incoming_to'])

        t=threading.Thread(target=self.jabbermain)
        t.setDaemon(1)
        t.start()
      

    def reloadroster(self):
        lock(self.mutex)

        self.roster = self.jabber.requestRoster()
        self.rosteraliascache = {}
        self.rosterjidcache = {}

        for p in self.roster.getJIDs():
            c = str(self.roster.getName(p))
            if c:
                self.rosterjidcache[str(p).upper()] = c
                self.rosteraliascache[c.upper()] = str(p)
                
        unlock(self.mutex)


        
    def sender_adress(self):
        res=u""
        if self.conf['resource']:
            res = u"/"+self.conf['resource']
        return self.conf['userid']+res

    def logout(self):
        # We hold conn_m lock already
        # (if we should need it)

        def ignore(*l,**kw):
            pass
        
        lock(self.mutex)
        personno = self.me
        textno = self.conf['config_source']
        self.alive = 0
        self.jabber.setDisconnectHandler(ignore)
        self.jabber.disconnect()
        log( "%s/%s requested disconnect." % (self.conf['userid'], self.conf['resource']) )
        unlock(self.mutex)

        if textno:
            conn.textstats.invalidate(textno)
        conn.conferences.invalidate(self.me)

    def send_config(self):        
        
        lock(self.mutex)
        c = self.conf
        dst = self.me
        debuginfo = ''
        unlock(self.mutex)
        
        lock(komsendq_m)
        komsendq.put( kommessage( dst, l1_e(
            u"Aktuell konfiguration som används: %s Debuginformation: %s." %
            (repr(c), debuginfo))))
        unlock(komsendq_m)




    def whoami(self):
        lock(self.mutex)
        i = self.conf['userid']
        unlock(self.mutex)
        return i

    def send_presence(self,show='',status='',type='',to=''):
        p = jabber.Presence()

        if show:
            p.setShow(show)
        if status:
            p.setStatus(status)
        if type:
            p.setType(type)

        totxt=''

        lock(self.mutex)
        if to:
            p.setTo(self.alias_to_uid(to))
            totext=' to %s' % p.getTo() 

        p.setFrom( self.sender_adress() )
        self.jabber.send(p)

        log( "%s sent presence%s." % (self.sender_adress(), totxt) )

        unlock(self.mutex)

    def directto(self,uid):
        lock(self.mutex)
        self.mode = 'chat'
        self.dst = uid
        unlock(self.mutex)


    def enter(self,roomname,server,nick):
        lock(self.mutex)
        self.mode = 'groupchat'
        self.dst = u'%s@%s' % (roomname, server)
        room = u'%s@%s/%s' % (roomname, server, nick)
        unlock(self.mutex)
        self.send_presence(to=room)
        return
        
    def leave(self):
        lock(self.mutex)
        self.mode = 'normal'
        unlock(self.mutex)


    def handle_message(self,sender,m):
        
        lock(self.mutex)
        currentmode = self.mode
        lastdst = self.lastdst
        lasttime = self.lasttime
        try:
            recpt_timeout = int(self.conf['def_recpt_time'])
        except ValueError:
            recpt_timeout = 30
        unlock(self.mutex)
            
        if currentmode == 'normal':
            if -1 == m.find(":"):
                to =''
            else:
                to = self.alias_to_uid( m[:m.find(":")].strip() )
                if -1 == to.find("@") or -1 != to.find(" "): # No JID?
                    to = ''
                    
            if (not lastdst or time.time()-lasttime>recpt_timeout) and not to:
                lock(komsendq_m)
                komsendq.put( kommessage( sender, l1_e(
                    u"Du måste ange mottagare följt av kolon innan meddelandet.")))
                unlock(komsendq_m)
                return
            elif lastdst and not to:
                to = lastdst
                tosend = m
                
                lock(self.mutex)
                self.lasttime = time.time()
                unlock(self.mutex)
            else:                
                tosend = m[m.find(":")+1:].strip()

                lock(self.mutex)
                self.lastdst = to
                self.lasttime = time.time()
                unlock(self.mutex)
                
            self.send_message(to,tosend,type='chat')

        elif currentmode == 'groupchat' or currentmode == 'chat':
            lock(self.mutex)
            dst = self.dst
            unlock(self.mutex)

            self.send_message(to=dst,type=currentmode,m=m)

        
    def send_message(self,to='',m='',type='chat',subject='',thread=''):
        # We hold conn_m lock already
        # (if we should need it)

        lock(self.mutex)
        dst = self.alias_to_uid(to)

        if -1 == dst.find("@"):
            kommsgto=self.me
            unlock(self.mutex)

            lock(komsendq_m)                
            komsendq.put(kommessage(kommsgto, l1_e(
                u"Felaktig adress: %s (originaladress %s)" % (dst,to))))
            
            unlock(komsendq_m)
            return

        msg = jabber.Message()

        if m:
            msg.setBody(m)

        if to:
            msg.setTo(dst)
        msg.setFrom( self.sender_adress() )

        if type:
            msg.setType(type)

        if subject:
            msg.setSubject(subject)

        if thread:
            msg.setThread(thread)

        self.jabber.send(msg)
        unlock(self.mutex)
        
        log( "%s sent message to %s." % (msg.getFrom(), msg.getTo()) )


    def is_ignored(self,s,type=''):
        # Should be called with self.mutex acquired

        check_in = self.conf['ignore']

        if type == 'presence':
            check_in = check_in + self.conf['ignore_presence']

        for p in check_in:
            if p[0:1] == '/' and p[-1:] == '/': # Regexp
                try:
                    if re.match(p[1:-1],str(s)):
                        return 1
                    if re.match(p[1:-1],str(s.getStripped())):
                        return 1
                except:
                    pass
            else:
                if str(s).lower() ==  p.lower() or \
                   str(s.getStripped()).lower() == p.lower():
                    return 1
            
        return 0



    def alias_to_uid(self,s):
        if s.upper() in self.rosteraliascache.keys():
            return self.rosteraliascache[s.upper()]

        if s.upper() in self.aliascache.keys():
            return self.aliascache[s.upper()]
        
        return s
    
    def uid_to_alias(self,s):
        if s.upper() in self.rosterjidcache.keys():
            return self.rosterjidcache[s.upper()]

        if s.upper() in self.jidcache.keys():
            return self.jidcache[s.upper()]

        return s


    def msg_sender(self,s):
        try:
            if self.conf['skip_resources']:
                return self.uid_to_alias(s.getStripped())
            if s.getResource():
                return self.uid_to_alias(s.getStripped())+"/"+s.getResource()
            return self.uid_to_alias(s.getStripped())
        except AttributeError,e:
            traceback.print_exception(e)
            stripped = str(s)
            su = stripped
            res = u""

            if -1 != su.find("/"):
                stripped = su[:su.find("/")]
                res = su[su.find("/"):]
                
            if self.conf['skip_resources']:
                return self.uid_to_alias(stripped)

            return self.uid_to_alias(stripped)+res
    
    def disconnected(self,j):
        lock(komsendq_m)
                
        komsendq.put(kommessage(self.me, l1_e(
            u"Jabberanslutning försvann, gissningsvis pga nätverksfel. "
            u"Det är rekommenderat att du ger kommandot 'disconnect' för att "
            u"hamna i ett känt tillstånd. ")))
        unlock(komsendq_m)

        self.alive = 0
        
        def ignore(*l,**kw):
            pass
        
        self.jabber.setDisconnectHandler(ignore)



    def got_message(self,j,m):
        # We should have lock for self.mutex

        log( "%s got message from %s." % (m.getTo(), m.getFrom()) )

        if not self.is_ignored(m.getFrom()):
            sendmsg = 0
            sendletter = 0
                       
            if self.conf['messages_only'] or \
               (not m.getThread() and not m.getSubject()) and \
               m.getType() != 'error' or m.getType() == 'groupchat':                   
                sendmsg = 1
                subj = u""

                if m.getSubject():
                    subj = u" (ang: %s)" % m.getSubject()
                    
                msg = u"%s%s: %s" % (
                    utf8_d(self.msg_sender(m.getFrom())),
                    subj,
                    utf8_d(m.getBody()))

            elif m.getType() == 'error':
                sendmsg = 1
                msg = u"FEL! Ditt meddelande till %s misslyckades: Fel '%s' (%s) " % (
                    utf8_d(self.msg_sender(m.getFrom())),
                    utf8_d(m.getError()),
                    utf8_d(m.getErrorCode()))

            elif m.getThread() or (not m.getType() and m.getSubject()):
                sendletter = 1
                
                if m.getSubject():
                    msg = u"%s\n%s" % (m.getSubject(), m.getBody())
                else:
                    msg = u"Meddelande från %s\n%s" % (self.msg_sender(m.getFrom()),
                                                       m.getBody())

                mi = kom.CookedMiscInfo()
                mi.recipient_list.append(kom.MIRecipient( kom.MIR_TO, self.me ))
                mi.recipient_list.append(kom.MIRecipient( kom.MIR_TO, daemon_person ))

                ai = []
                aient = kom.AuxItem(kom.AI_CREATING_SOFTWARE)
                aient.data = u"Canidius %s " % VERSION
                ai.append( aient )

                if m.getThread():
                    # TODO: Should really use private aux-items
                    aient = kom.AuxItem(AI_CAN_THREAD)
                    aient.data = u"%s" % m.getThread()
                    aient.flags.inherit = 1
                    ai.append(aient)

                aient = kom.AuxItem(kom.AI_CONTENT_TYPE)
                aient.data = u"text/plain;charset=utf-8"
                ai.append(aient)

                aient = kom.AuxItem(kom.AI_MX_FROM)
                aient.data = m.getFrom().getStripped()
                ai.append(aient)

                if self.uid_to_alias( m.getFrom().getStripped() ) != str(m.getFrom().getStripped()):
                    aient = kom.AuxItem(kom.AI_MX_AUTHOR)
                    aient.data = u"%s" % (self.uid_to_alias( m.getFrom().getStripped()))
                    ai.append(aient)

                aient = kom.AuxItem(AI_CAN_FROM)
                aient.data = u"%s" % m.getFrom()
                ai.append(aient)

                aient = kom.AuxItem(kom.AI_MX_TO)
                aient.data = u"%s" % m.getTo().getStripped()
                ai.append(aient)

                aient = kom.AuxItem(AI_CAN_TO)
                aient.data = u"%s" % m.getTo()
                ai.append(aient)


            else:
                sendmsg = 1
                msg = u"Konstigt meddelande, rått: %s " % repr(m)

            if sendmsg:
                lock(komsendq_m)                
                komsendq.put(kommessage(self.me, l1_e(msg)))
                unlock(komsendq_m)

            if sendletter:
                lock(komsendq_m)
                komsendq.put(komtext(utf8_e(msg), mi, ai, m.getThread()))
                unlock(komsendq_m)

            

        
    def got_presence(self,j,m):
        log( "%s got presence from %s." % (m.getTo(), m.getFrom()) )

        if not self.is_ignored(m.getFrom(), 'presence'):

            stattext = u""
            if m.getStatus():
                stattext = u" (%s)" % m.getStatus() 
            
            showtext = u""
            if m.getShow():
                showd = {'away':u' men borta just nu',
                         'chat':u' och pratig',
                         'dnd':u' men vill inte bli störd',
                         'xa':u' men är borta ett tag framåt.'}
                showtext = showd[m.getShow()]


            if m.getType()=='unavailable':
                msg = u"%s är utloggad%s%s." % (self.msg_sender(m.getFrom()), 
                                                 showtext,
                                                 stattext)
            elif not m.getType():
                msg = u"%s är inloggad%s%s." % (self.msg_sender(m.getFrom()),
                                                  showtext,
                                                  stattext)                
            else:
                msg = u"%s har konstig typ (%s) eller status (%s) (rått: %s)" % (
                    m.getFrom().getStripped(),
                    m.getType(),
                    m.getStatus(),
                    repr(m))
                

            lock(komsendq_m)                
            komsendq.put(kommessage(self.me, l1_e(msg)))
            unlock(komsendq_m)
                   
        
    def got_iq(self,j,m):
        log( "%s got iq from %s." % (m.getTo(), m.getFrom()) )
       
        msg = u"IQ: %s " % repr(m)

        lock(komsendq_m)                
        komsendq.put(kommessage(self.me, l1_e(msg)))
        unlock(komsendq_m)


    def jabbermain(self):
        lock(self.mutex)

        try:
            self.jabber = jabber.Client(self.conf['server'], int(self.conf['port']) )
            self.jabber.connect()
        except socket.error, e:
            lock(komsendq_m)
                
            komsendq.put(kommessage(self.me, l1_e(
                u"Anslutningen till Jabberservern misslyckades, gissningsvis pga nätverksfel. "
                u"Felet var '%s' vid anslutning till %s:%s. " 
                u"Det är rekommenderat att du ger kommandot 'disconnect' för att "
                u"hamna i ett känt tillstånd."
                % (e.args[1], str(self.conf['server']), str(self.conf['port']) ) )))
            unlock(komsendq_m)
            return
        
        self.jabber.registerHandler('message',self.got_message)
        self.jabber.registerHandler('presence',self.got_presence)
        self.jabber.registerHandler('iq',self.got_iq)

        self.jabber.setDisconnectHandler(self.disconnected)

        try:
            self.jabber.auth( self.conf['userid'],
                              self.conf['password'],
                              self.conf['resource'])
            self.jabber.sendPresence( status = self.conf['startup_status'],
                                      show = self.conf['startup_show'])
        except AttributeError, e:
            lock(komsendq_m)
            komsendq.put(kommessage(self.me, l1_e(
                u"Jabberanslutning misslyckades, gissningsvis pga nätverksfel. "
                u"Det är rekommenderat att du ger kommandot 'disconnect' för att "
                u"hamna i ett känt tillstånd. (Felinfo: %s)" % repr(e))))
            unlock(komsendq_m)


        self.lastdst = ''
        self.lasttime = 0
        self.mode = 'normal'

        self.rosteraliascache = {}
        self.rosterjidcache = {}

        self.aliascache = {}
        self.jidcache = {}

        for (jid,name) in self.conf['aliases']:
            self.aliascache[jid.upper()] = name
            self.jidcache[name.upper()] = jid

        self.alive = 1
        person_no = self.realme
        
        unlock(self.mutex)

        self.reloadroster()

        log( "%s/%s (person %d) logged in to %s:%s." % (self.conf['userid'],
                                                        self.conf['resource'],
                                                        person_no,
                                                        self.conf['server'],
                                                        self.conf['port']) )
        # TODO: Send session-initiate stanza?
        
        #for p in self.conf['aliases']:
        #    self.jabber.send( jabber.Presence


        while self.alive:
            lock(self.mutex)
            self.jabber.process(0)
            unlock(self.mutex)
            time.sleep(0.5)





        
def away_handler( msg, conn, p, pers_no=0 ):
    p.send_presence('away',msg)
    return 1

def dnd_handler( msg, conn, p, pers_no=0 ):
    p.send_presence('dnd',msg)
    return 1

def back_handler( msg, conn, p, pers_no=0 ):
    p.send_presence('',msg)
    return 1

def chat_handler( msg, conn, p, pers_no=0 ):
    p.send_presence('chat',msg)
    return 1

def xa_handler( msg, conn, p, pers_no=0 ):
    p.send_presence('xa',msg)
    return 1

def status_handler( msg, conn, p, pers_no=0 ):
    p.send_presence(type='probe',to=msg)
    kommessage(pers_no, l1_e( u"Statusförfrågan skickad.")).send(conn)
    return 0
    
def disconnect_handler( msg, conn, p, pers_no ):
    p.logout()
    lock(threaddict_m)
    del threaddict[pers_no]
    unlock(threaddict_m)

    lock(sessdict_m)
    del sessdict[pers_no]
    unlock(sessdict_m)

    kommessage(pers_no, l1_e( u"Anslutningen är nerkopplad.")).send(conn)
    return 0

def ping_handler( msg, conn, p, pers_no=0 ):
    kommessage(pers_no, l1_e( u"Pong")).send(conn)
    return 0

def config_handler( msg, conn, p, pers_no=0 ):
    p.send_config()
    return 0

def enter_handler( msg, conn, p, pers_no=0 ):
    l = msg.split()

    p.enter(l[0],l[1],l[2])
    kommessage(pers_no, l1_e( u"Försöker gå in i rummet %s på servern %s som %s (ifall "
                              u"det inte går måste du ändå lämna rummet för att agera normalt)."
                              % (
        l[0],
        l[1],
        l[2]))).send(conn)
    return 0

def direct_handler( msg, conn, p, pers_no=0 ):
    l = msg.split()

    p.directto(l[0])
    kommessage(pers_no, l1_e( u"Skickar allt du skriver till %s, ge kommandot lämna för att återgå "
                              u"till normalt läge." % l[0] )).send(conn)
    return 0

def leave_handler( msg, conn, p, pers_no=0 ):
    p.leave()
    kommessage(pers_no, l1_e( u"Återgår till normalläge." )).send(conn)
    return 0


msg_handlers={'xa':xa_handler,
              'borta ett tag':xa_handler,
              'away':away_handler,
              'borta':away_handler,
              'dnd':dnd_handler,
              'stör ej':dnd_handler,
              'back':back_handler,
              'tillbaka':back_handler,
              'chat':chat_handler,
              'prat':chat_handler,
              'pratig':chat_handler,
              'disconnect':disconnect_handler,
              'koppla ner':disconnect_handler,
              'ping':ping_handler,
              'enter':enter_handler,
              'gå in i':enter_handler,
              'gå ut ur':leave_handler,
              'leave':leave_handler,
              'lämna':leave_handler,
              'prata med':direct_handler,
              'direct':direct_handler,
              'config':config_handler,
              'konfiguration':config_handler,
              'status':status_handler
              }

def async_message( msg, conn ):

    if not msg.recipient == daemon_person:   # Not a message to us?
        return

    lock(threaddict_m)
    already_regged = msg.sender in threaddict.keys()
    unlock(threaddict_m)
    
    if already_regged:
        # Handle better later TODO

        lock(threaddict_m)
        p = threaddict[msg.sender]
        unlock(threaddict_m)

        try:
            text = utf8_d( msg.message.strip() )
        except UnicodeDecodeError:
            text = l1_d( msg.message.strip() )

        for q in msg_handlers.keys():
            if text[0:1] == '/' and (text[1:] == q or text[1:].startswith(q+' ')):
                if msg_handlers[q](text[1+len(q):].strip(),conn, p, msg.sender):
                    kommessage( msg.sender, l1_e(u"Närvarostatus skickad." )).send(conn)
                return

        p.handle_message(msg.sender, text)
    else:
        c = check_active(msg.sender)

        if c: 
            notice_person( c, msg.sender, conn )
            
            kommessage( msg.sender, l1_e(
                u"Nu har jag registrerat att du är här (visste jag inte förut).")).send(conn)
        
            # Begin and handle the message from the beginning
            async_message(msg,conn)

        else:
            kommessage( msg.sender, l1_e(
                u"Se min presentation för att få veta hur man använder mig.")).send(conn)



    return



def async_new_recipient( m, conn ):
    if m.conf_no == daemon_person: # Ignore if we're not the new one
        class my_new_text:
            def __init__(self, text_no):
                self.text_no = text_no
                self.text_stat = conn.textstats[text_no]
        async_new_text( my_new_text(m.text_no), conn )
        

def async_new_text( m, conn ):

    tno = m.text_no
    ts = m.text_stat

    for p in ts.misc_info.recipient_list:
        if p.recpt == daemon_person: # We are members of no other confs
            try:
                kom.ReqMarkAsRead( conn, daemon_person, [p.loc_no] ).response()
            except:
                pass

    if ts.author == daemon_person: # Ignore what we wrote
        return
    
    tous = 0

    for p in ts.misc_info.recipient_list:
        if p.recpt == daemon_person:
            tous = 1

    if not tous:   # Not a message to us?
        return

    lock(threaddict_m)
    already_regged = ts.author in threaddict.keys()
    unlock(threaddict_m)
    
    if already_regged:
        # Handle better later TODO

        lock(threaddict_m)
        pers = threaddict[ts.author]
        unlock(threaddict_m)

        to = ""
        thread = ""

        # Look in message first
        for q in ts.aux_items:
            if q.tag == kom.AI_MX_TO:
                to = q.data
            elif q.tag == AI_CAN_TO:
                to = q.data
            elif q.tag == AI_CAN_THREAD:
                thread = q.data

        # Check comments if we found nothing.
        if not to:
            for p in ts.misc_info.comment_to_list:
                try:
                    if conn.textstats[p.text_no].author == daemon_person:
                        for q in conn.textstats[p.text_no].aux_items:
                            if q.tag == AI_CAN_FROM:
                                to = q.data
                            if q.tag == kom.AI_MX_FROM:
                                to = q.data
                            elif q.tag == AI_CAN_THREAD:
                                thread = q.data
                except kom.NoSuchText:
                    pass
            
        if not to: # Don't know who to send to?
            return

        dst = to
        if addrre.match(to):
            dst = addrre.match(to).groups()[0]

        text = kom.ReqGetText(conn,
                              tno,
                              0, ts.no_of_chars).response()

        for p in ts.aux_items:
            if p.tag == kom.AI_CONTENT_TYPE:
                pos = p.data.upper().find("CHARSET=")
                if pos != -1:
                    charset = p.data[pos+8:].strip()
                    if -1 != charset.find(";"):
                        charset = charset[:charset.find(";")].strip()

        try:
            text = encodings.search_function(charset)[1](text)[0]
            
        except:
            text = l1_d( msg.message.strip() )

        tl = text.split("\n")        
        pers.send_message(dst,"\n".join(tl[1:]),type='',subject=tl[0],thread=thread)

        ai1 = kom.AuxItem(kom.AI_MX_TO)
        ai1.data = to

        ai2 = kom.AuxItem(kom.AI_MX_FROM)
        ai2.data = pers.whoami()

        ai3 = kom.AuxItem(AI_CAN_TO)
        ai3.data = dst

        try:
            kom.ReqModifyTextInfo(conn, tno, [], [ai1,ai2,ai3]).response()
        except:
            pass



def async_login( p, conn ):

    if p.person_no and p.session_no:

        c = None

        lock(threaddict_m)
        regged = p.person_no in threaddict.keys()
        unlock(threaddict_m)
        
        if not regged:
            c = check_active( p.person_no )

        notice_person( c, p.person_no, conn )            


def async_logout( p, conn ):

    if p.person_no and p.session_no:

        lock(sessdict_m)
        # User we care about?

        if sessdict.has_key(p.person_no):
            # Yes, update view.

            unlock(sessdict_m)
            notice_person( None, p.person_no, conn )
            lock(sessdict_m)
                               
            if not sessdict[p.person_no]:
                lock(threaddict_m)
                if threaddict.has_key(p.person_no):
                    threaddict[p.person_no].logout()
                    del threaddict[p.person_no]
                del sessdict[p.person_no]
                unlock(threaddict_m)
                                         
        unlock(sessdict_m)


def notice_person( pers, pers_no, conn, oncache=None ):
    # We should have conn_m lock

    lock(threaddict_m)

    if pers and pers_no not in threaddict.keys():
        # Should always be the case.
        if not threaddict.has_key( pers_no ):
            threaddict[ pers_no ] = pers

    unlock(threaddict_m)

    if not oncache:
        oncache = kom.ReqWhoIsOnDynamic(conn).response()
        
    whoison = filter(lambda x: x.person == pers_no, oncache )                             
    sessions = map( lambda x: x.session, whoison)

    lock(sessdict_m)
        
    sessdict[pers_no]=sessions

    unlock(sessdict_m)




log( "Canidius started" )
        
conn_m = mutex.mutex()
lock(conn_m)

conn = kom.CachedConnection(KOMSERVER, 4894)


persons = conn.lookup_name(AGENT_PERSON, want_pers = 1, want_confs = 0)
if len(persons) != 1:
    print "Can't find myself - not just one match"
else:
    daemon_person = persons[0][0]

                                  
kom.ReqLogin(conn, daemon_person, AGENT_PASSWORD, invisible = 1).response()

conn.add_async_handler(kom.ASYNC_SEND_MESSAGE, async_message)
conn.add_async_handler(kom.ASYNC_LOGOUT, async_logout)
conn.add_async_handler(kom.ASYNC_LOGIN, async_login)
conn.add_async_handler(kom.ASYNC_NEW_TEXT, async_new_text)
conn.add_async_handler(kom.ASYNC_NEW_RECIPIENT, async_new_recipient)


kom.ReqAcceptAsync(conn, [kom.ASYNC_SEND_MESSAGE,]).response()
kom.ReqAcceptAsync(conn, [kom.ASYNC_LOGOUT,
                          kom.ASYNC_SEND_MESSAGE,
                          kom.ASYNC_NEW_RECIPIENT,
                          kom.ASYNC_NEW_TEXT,
                          kom.ASYNC_LOGIN
                          ]).response()

kom.ReqSetClientVersion(conn, "Canidius %s", VERSION)

lastkeys=[]



onnow = kom.ReqWhoIsOnDynamic(conn).response()
persons = map( lambda x:x.person, onnow )
persons.sort()

# Remove duplicates

persons = [persons[0]] + [persons[i] for i in range(1, len(persons))
                          if persons[i] != persons[i - 1]]


for p in persons:
    c = check_active( p )

    if c: 
        notice_person( c, p, conn, onnow )
unlock(conn_m)


while 1:

    lock(conn_m)
    conn.parse_present_data()

    lock(komsendq_m)                
    try:
        while 1:
            komsendq.get_nowait().send(conn)
    except Queue.Empty:
        pass    
    unlock(komsendq_m)
        
    unlock(conn_m)
        
    time.sleep(0.5)
