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

AGENT_PERSON = "Pontus Testperson"
KOMSERVER = "kom.lysator.liu.se"
logfile = open("/tmp/canidius.log", 'a')
               
import sys

# Can we get around this somehow?

if hasattr(sys,'setdefaultencoding'):
    sys.setdefaultencoding("latin-1")
else:
    print "Warning: Can't change system default encoding, unsupported operation!"
    
import jabber
import kom
import os
import mutex
import threading
import time
import traceback
import encodings
import Queue

homed = os.getenv("HOME")

if not homed:   # No such environment variable
    homed = ""
    
AGENT_PASSWORD = open( homed + "/."+ AGENT_PERSON + "_password" ).readline().strip()

daemon_person = -1  # Will be looked up

VERSION = "0.1 $Id: canidius.py,v 1.2 2004/11/30 10:35:21 _cvs_pont_tel Exp $"


komsendq = Queue.Queue()
komsendq_m = mutex.mutex()

sessdict = {}
sessdict_m = mutex.mutex()

threaddict = {}
threaddict_m = mutex.mutex()

log_m = mutex.mutex()


def log(s):
    lock(log_m)
    if logfile:
        logfile.write("%s %s\n" % (time.ctime(),s))
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
        
        kom.ReqSendMessage(c, self.to, self.msg ).response()

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
                    if p.tag == kom.AI_MX_MESSAGE_ID and p.data == '<%s>' % self.thread:
                        return 1

            possible_texts = messages_satisfying( rightthread )

            if possible_texts: # Any texts with this thread?
                possible_texts.reverse() # Take the latest
                
                self.miscinfo.comment_to_list.append(
                    kom.MICommentTo(kom.MIC_COMMENT,possible_texts[0]))
            

        kom.ReqCreateText(conn,
                          self.text,
                          self.miscinfo,
                          self.auxitems).response()



    
def lock(m):
    while not m.testandset():
        time.sleep(0.1)

def unlock(m):
    m.unlock()

def parse_configmessage(text, report=0):
    # Should probably be in person
    tl = text.split("\n")
    nounderstand = []
    conf = {'aliases':[],
            'ignore':[],
            'ignore_presence':[],
            'sendpresence':[],
            'startup_show':'',
            'startup_status':''}
    
    if -1 != tl[0].lower().find("jabberconfig"): # Configuration letter
        for p in tl:
            if len(p) and p[0] != '#':
                treated = 0

                for q in ('server','userid','password','alias','resource',
                          'port','skip_resources''ignore','ignore_presence',
                          'sendpresence','startup_show','startup_status',
                          'divert_incoming_to'):
                    l = filter(None, p.lower().split())
                    if l and l[0] == q:
                        if q == 'alias':
                            origcasel = filter(None, p.split())
                            conf['aliases'].append((origcasel[1],origcasel[2]))
                            treated = 1
                        elif q in ('ignore','ignore_presence','sendpresence'):
                            for r in l[1:]:
                                conf[q].append(r)
                        else:
                            conf[q] = l[1]
                            treated = 1

                if not treated:
                    nounderstand.append(p)

    if nounderstand and report:
        pass # TODO

    sp = conf.keys()

    if 'server' in sp and 'userid' in sp and 'password' in sp:
        if not 'port' in sp:
            conf['port'] = 5222
        if not 'resource' in sp:
            conf['resource'] = 'Lyskom'
        if not 'skip_resources' in sp:
            conf['skip_resources'] = 'Lyskom'

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
        
        textmap = kom.ReqLocalToGlobal(conn,
                                       daemon_person,
                                       baselocal,
                                       search_now).response()

        for p in textmap.list:
            globtext = p[1]

            if testfunc( conn.textstats[p[1]] ):
                possible_texts.append(globtext)
                            
        texts_to_search = texts_to_search - search_now


    return possible_texts


    
def configmessage(person_no):

    def right_author_and_recpt(ts):
        # TODO: Allow for setting a private aux-item on the person to point
        # to configuration message. Also only check messages marked with
        # a "configuration" aux-item.
        if ts.author == person_no:
            for q in ts.misc_info.recipient_list:
                if person_no == q.recpt:
                    return 1

    possible_texts = messages_satisfying( right_author_and_recpt )

    if possible_texts:

        possible_texts.reverse() # Last text first
        
        for globtext in possible_texts:
            
            text = kom.ReqGetText(conn,
                                  globtext,
                                  0, conn.textstats[globtext].no_of_chars).response()

            config = parse_configmessage(text)
                        
            if config:
                #unlock(conn_m)
                return person(person_no,config)


    #unlock(conn_m)

def check_active(person_no):
    return configmessage(person_no)

class person:
    def __init__(self, person_no,conf):
        self.me = person_no
        self.mutex = mutex.mutex()
        self.conf = conf
        
        if conf.has_key('divert_incoming_to'):
            self.me = int(conf['divert_incoming_to'])

        self.jabber = jabber.Client(conf['server'], conf['port'])
        self.jabber.connect()
        
        self.jabber.registerHandler('message',self.got_message)
        self.jabber.registerHandler('presence',self.got_presence)
        self.jabber.registerHandler('iq',self.got_iq)

        self.jabber.setDisconnectHandler(self.disconnected)
        self.jabber.auth( conf['userid'], conf['password'], conf['resource'])
        self.jabber.sendPresence(status=conf['startup_status'], show=conf['startup_show'])

        self.alive = 1

        log( "%s/%s (person %d) logged in to %s:%s." % (conf['userid'], conf['resource'], person_no,
                                                        conf['server'], conf['port']) )
        # TODO: Send session-initiate stanza?
        
        #for p in self.conf['aliases']:
        #    self.jabber.send( jabber.Presence
        t=threading.Thread(target=self.jabberloop)
        t.setDaemon(1)
        t.start()
      

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
        self.alive = 0
        self.jabber.setDisconnectHandler(ignore)
        self.jabber.disconnect()
        log( "%s/%s requested disconnect." % (self.conf['userid'], self.conf['resource']) )
        unlock(self.mutex)




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




        
    def send_message(self,to,m,type='chat',subject='',thread=''):
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
        msg.setBody(m)
        msg.setTo(dst)
        msg.setFrom( self.sender_adress )

        if type:
            msg.setType(type)

        if subject:
            msg.setSubject(subject)

        if thread:
            msg.setThread(thread)
        
        self.jabber.send(msg)
        unlock(self.mutex)
        
        log( "%s sent message to %s." % (msg.getFrom(), msg.getTo()) )




    def alias_to_uid(self,s):
        for p in self.conf['aliases']:
            if p[0].upper() == s.upper():
                return p[1]
        return s
    
    def uid_to_alias(self,s):
        for p in self.conf['aliases']:
            if p[1].upper() == s.upper():
                return p[0]
        return s


    def msg_sender(self,s):
        try:
            if self.conf['skip_resources']:
                return self.uid_to_alias(s.getStripped())
            return self.uid_to_alias(s.getStripped())+"/"+s.getResource()
        except AttributeError:
            stripped = s
            su = stripped
            res = u""

            if -1 != su.find("/"):
                stripped = su[:su.find("/")]
                res = su[su.find("/"):]
                
            if self.conf['skip_resources']:
                return self.uid_to_alias(stripped)

            return uid_to_alias(stripped)+res
    
    def disconnected(self,j):
        lock(komsendq_m)
                
        komsendq.put(kommessage(self.me, l1_e(
            u"Jabberanslutning försvann, gissningsvis pga nätverksfel")))
        unlock(komsendq_m)

        self.alive = 0
        
        def ignore(*l,**kw):
            pass
        
        self.jabber.setDisconnectHandler(ignore)



    def got_message(self,j,m):
 
        log( "%s got message from %s." % (m.getTo(), m.getFrom()) )

        if not str(m.getFrom().getStripped()) in self.conf['ignore']:
            sendmsg = 0
            sendletter = 0
                       
            if  self.conf['messages_only'] or \
               (not m.getThread() and not  m.getSubject()) and \
               m.getType() != 'error':                   
                sendmsg = 1
                msg = u"Meddelande från %s: %s" % (
                    utf8_d(self.msg_sender(m.getFrom())),
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
                    aient = kom.AuxItem(kom.AI_MX_MESSAGE_ID)
                    aient.data = u"<%s>" % m.getThread()
                    aient.flags.inherit = 1
                    ai.append(aient)

                aient = kom.AuxItem(kom.AI_CONTENT_TYPE)
                aient.data = u"text/plain;charset=utf-8"
                ai.append(aient)


                aient = kom.AuxItem(kom.AI_MX_FROM)
                aient.data = m.getFrom().getStripped()
                ai.append(aient)

                aient = kom.AuxItem(kom.AI_MX_TO)
                aient.data = m.getTo().getStripped()
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

        if not (str(m.getFrom().getStripped()) in self.conf['ignore'] or 
                str(m.getFrom().getStripped()) in self.conf['ignore_presence']):

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


            res = u"(%s) " % m.getFrom().getResource()

            if self.conf['skip_resources']:
                res = u""

            if m.getType()=='unavailable':
                msg = u"%s %sär utloggad%s%s." % (self.msg_sender(m.getFrom()),
                                                 res,
                                                 showtext,
                                                 stattext)
            elif not m.getType():
                msg = u"%s %sär inloggad%s%s." % (self.msg_sender(m.getFrom()),
                                                  res,
                                                  showtext,
                                                  stattext)                
            else:
                msg = u"%s %shar konstig typ (%s) eller status (%s) (rått: %s)" % (
                    m.getFrom().getStripped(),
                    res,
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


    def jabberloop(self):
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
    return 0

def ping_handler( msg, conn, p, pers_no=0 ):
    kommessage(pers_no, l1_e( u"Pong")).send(conn)
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
            if text == q or text.startswith(q+' '):
                if msg_handlers[q](text[len(q):].strip(),conn, p, msg.sender):
                    kommessage( msg.sender, l1_e(u"Närvarostatus skickad." )).send(conn)
                return

        if -1 == text.find(":"):
            kommessage( msg.sender, l1_e(
                u"Du måste ange mottagare följt av kolon innan meddelandet.")).send(conn)
            return

        to = text[:text.find(":")].strip()
        tosend = text[text.find(":")+1:].strip()

        p.send_message(to,tosend,type='chat')
        
    else:
        c = check_active(msg.sender)

        if c: 
            lock(threaddict_m)
            if msg.sender not in threaddict.keys():
                # Should always be the case.
                threaddict[msg.sender]=c
            unlock(threaddict_m)

            lock(sessdict_m)
            whoison = filter(lambda x: x.person == msg.sender,
                             kom.ReqWhoIsOnDynamic(conn).response())
            sessions = map( lambda x: x.session, whoison)
            sessdict[msg.sender]=[sessions]

            unlock(sessdict_m)

            kommessage( msg.sender, l1_e(
                u"Nu har jag registrerat att du är här (visste jag inte förut).")).send(conn)

            # Begin and handle the message from the beginning
            async_message(msg,conn)

        else:
            kommessage( msg.sender, l1_e(
                u"Se min presentation för att få veta hur man använder mig.")).send(conn)





    return

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
            elif q.tag == kom.AI_MX_MESSAGE_ID:
                thread = q.data[1:-1]

        # Check comments if we found nothing.
        if not to:
            for p in ts.misc_info.comment_to_list:
                try:
                    if conn.textstats[p.text_no].author == daemon_person:
                        for q in conn.textstats[p.text_no].aux_items:
                            if q.tag == kom.AI_MX_FROM:
                                to = q.data
                            elif q.tag == kom.AI_MX_MESSAGE_ID:
                                thread = q.data[1:-1]
                except kom.NoSuchText:
                    pass
            
        if not to: # Don't know who to send to?
            return 

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
        pers.send_message(to,"\n".join(tl[1:]),type='',subject=tl[0],thread=thread)

        ai1 = kom.AuxItem(kom.AI_MX_TO)
        ai1.data = to

        ai2 = kom.AuxItem(kom.AI_MX_FROM)
        ai2.data = pers.whoami()

        try:
            kom.ReqModifyTextInfo(conn, tno, [], [ai1,ai2]).response()
        except:
            pass



def async_login( p, conn ):

    if p.person_no and p.session_no:

        c = check_active(p.person_no)

        if c:
            lock(sessdict_m)
            if p.person_no in sessdict.keys():
                sessdict[p.person_no].append(p.session_no)
            else:
                sessdict[p.person_no]=[p.session_no]
            unlock(sessdict_m)
            
            lock(threaddict_m)
            if p.person_no not in threaddict.keys():
                threaddict[p.person_no]=c
            unlock(threaddict_m)
            


def async_logout( p, conn ):

    if p.person_no and p.session_no:
 
        lock(sessdict_m)
               
        if p.person_no in sessdict.keys() and \
               p.session_no in sessdict[p.person_no]:
            sessdict[p.person_no].remove(p.session_no)

            if not sessdict[p.person_no]:
                lock(threaddict_m)
                threaddict[p.person_no].logout()
                del threaddict[p.person_no]
                del sessdict[p.person_no]
                unlock(threaddict_m)
                                         
        unlock(sessdict_m)
      


log( "Canidius started" )
        
conn_m = mutex.mutex()
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

kom.ReqAcceptAsync(conn, [kom.ASYNC_SEND_MESSAGE,]).response()
kom.ReqAcceptAsync(conn, [kom.ASYNC_LOGOUT,
                          kom.ASYNC_SEND_MESSAGE,
                          kom.ASYNC_NEW_TEXT,
                          kom.ASYNC_LOGIN
                          ]).response()

kom.ReqSetClientVersion(conn, "Canidius %s", VERSION)

lastkeys=[]

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
