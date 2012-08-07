#!/usr/bin/python
# -*- coding: utf-8 -*-

# tamaclient.py
# This file is part of tama
# 
# Copyright (C) 2012 - Enrico Polesel
# 
# tama is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# any later version.
# 
# tama is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with tama. If not, see <http://www.gnu.org/licenses/>.

import os
#~ import sqlalchemy
#~ from sqlalchemy.ext.declarative import declarative_base
#~ from sqlalchemy.orm import sessionmaker
import thread
import socket
import signal
import subprocess
import datetime

debug = 4
PID_FILE_PATH = "tamaclientar51.pid"
#AUTH_DB_PATH = "auth.db"
TAMA_DIR = "/afs/uz.sns.it/user/enrico/private/tama/"
#AUTH_LOG_PATH = 'auth.log'
PORT = 12345

def debugMessage (level, msg):
    if level <=debug:
        print "[Tamaclientar51 - debug] "+str(msg)
        

if os.path.exists(PID_FILE_PATH):
        debugMessage(1, "Tamaclient is already running, exiting")
        exit(0)
else:
        pid_file = open(PID_FILE_PATH, "w")
        pid_file.write(str(os.getpid())+"\n")
        pid_file.close()

#~ engine = sqlalchemy.create_engine('sqlite:///'+AUTH_DB_PATH)
#~ Base = declarative_base()

#~ class Event (Base):
    #~ __tablename__ = 'events'
    #~ 
    #~ id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    #~ date = sqlalchemy.Column(sqlalchemy.DateTime)
    #~ action = sqlalchemy.Column(sqlalchemy.String)
    #~ user = sqlalchemy.Column(sqlalchemy.String)
    #~ program = sqlalchemy.Column(sqlalchemy.String)
    #~ source = sqlalchemy.Column(sqlalchemy.String)
    #~ source_ip = sqlalchemy.Column(sqlalchemy.String)
    #~ 
    #~ def __init__ (self, date, action, user, program, source, source_ip):
        #~ self.date = date
        #~ self.action = action
        #~ self.user = user
        #~ self.program = program
        #~ self.source = source
        #~ self.source_ip = source_ip

#~ Base.metadata.create_all(engine) 
#~ Session = sessionmaker(bind=engine)
#~ session = Session()

#~ if os.path.isfile(AUTH_LOG_PATH+".1"):
    #~ os.system(TAMA_DIR+"tamaauth.py "+AUTH_LOG_PATH+".1")
#~ os.system(TAMA_DIR+"tamaauth.py "+AUTH_LOG_PATH)
#~ start_event = Event(datetime.datetime.today(),"start","tama","tamaclient",socket.gethostname(),"")
#~ session.add(start_event)
#~ session.commit()


def connectedUser():
    #~ # Count session opened and closed from the last tamaclient start
    #~ opened = session.query(Event.action).filter(Event.id > start_id).filter(Event.action=='open').filter(Event.user != 'lightdm').count()
    #~ closed = session.query(Event.action).filter(Event.id > start_id).filter(Event.action=='close').filter(Event.user != 'lightdm').count()
    #~ return opened - closed
    (stdout, stderr) = subprocess.Popen([TAMA_DIR+"tamauserar51.sh",""], stdout=subprocess.PIPE).communicate()
    return stdout

def temperature(n):
    (stdout, stderr) = subprocess.Popen([TAMA_DIR+"tamatemp.sh","0"], stdout=subprocess.PIPE).communicate()
    return stdout


def connection(conn):
    #~ start_id = start_event.id
    debugMessage(4,"new connection")
    #~ if os.path.isfile(AUTH_LOG_PATH+".1"):
        #~ os.system(TAMA_DIR+"tamaauth.py "+AUTH_LOG_PATH+".1")
    #~ os.system(TAMA_DIR+"tamaauth.py "+AUTH_LOG_PATH)
    debugMessage(4,"starting while for incoming orders")
    while(1):
        string=conn.recv(1024)
        debugMessage(4,"recived string "+string)
        if not string: break
        string = string.rstrip('\n')
        if string == 'connected':
            debugMessage(4,"executing connectedUser()")
            conn.send(str(connectedUser())+"\n")
        elif string == 'temp0':
            debugMessage(4,"execuiting temperature(0)")
            conn.send(str(temperature(0))+"\n")
        elif string == 'ciao':
            conn.send("Ciao anche a te\n")
        elif string == 'quit' or string == 'exit':
            break
        else:
            conn.send("Unknow order: \""+string+"\"\n")
    debugMessage(4,"closing connection")
    conn.close()



s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind (( "" , PORT ))
s.listen(5)

def sigExit(signum, frame):
    debugMessage(4, "closing socket")
    s.shutdown(socket.SHUT_RDWR)
    s.close()
    debugMessage(4,"socket close, bye bye")
    
    #stop_event = Event(datetime.datetime.today(),"stop","tama","tamaclient",socket.gethostname(),"")
    #session.add(stop_event)
    #session.commit()
    os.remove(PID_FILE_PATH)
    exit(0)

signal.signal(signal.SIGTERM,sigExit)
signal.signal(signal.SIGINT,sigExit)

while (1):
    conn, addr = s.accept()
    thread.start_new_thread ( connection , ( conn ,) )


os.remove(PID_FILE_PATH)
