#!/usr/bin/python

# tamaauth.py
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



from logsparser.lognormalizer import LogNormalizer as LN
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os
import sys

debug = 4
PID_FILE_PATH = "tamaauth.pid"
AUTH_DB_PATH = "auth.db"
AUTH_LOG_PATH = "auth.log"

def debugMessage (level, msg):
    if level <=debug:
        print "[Tamaauth - debug] "+str(msg)
        

if os.path.exists(PID_FILE_PATH):
        debugMessage(1, "Tamaauth is already running, exiting")
        exit(0)
else:
        pid_file = open(PID_FILE_PATH, "w")
        pid_file.write(str(os.getpid())+"\n")
        pid_file.close()

if len(sys.argv)>1:
    AUTH_LOG_PATH = sys.argv[1]

debugMessage(2,"Parsing "+AUTH_LOG_PATH+" as auth.log")


normalizer = LN('/usr/local/lib/python2.7/dist-packages/pylogsparser-0.4-py2.7.egg/share/logsparser/normalizers')

engine = sqlalchemy.create_engine('sqlite:///'+AUTH_DB_PATH)
Base = declarative_base()


class Event (Base):
    __tablename__ = 'events'
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    date = sqlalchemy.Column(sqlalchemy.DateTime)
    action = sqlalchemy.Column(sqlalchemy.String)
    user = sqlalchemy.Column(sqlalchemy.String)
    program = sqlalchemy.Column(sqlalchemy.String)
    source = sqlalchemy.Column(sqlalchemy.String)
    source_ip = sqlalchemy.Column(sqlalchemy.String)
    
    def __init__ (self, date, action, user, program, source, source_ip):
        self.date = date
        self.action = action
        self.user = user
        self.program = program
        self.source = source
        self.source_ip = source_ip
    

Base.metadata.create_all(engine) 
Session = sessionmaker(bind=engine)
session = Session()
if session.query(Event).count() == 0:
    mindate = datetime.datetime(1970,1,1,0,0,0)
else:
    mindate = session.query(sqlalchemy.func.max(Event.date)).scalar()
debugMessage(3,"Mindate: "+str(mindate))

try:
    log_file = open(AUTH_LOG_PATH, 'r')
except:
    debugMessage(1,AUTH_LOG_PATH+" not found, exiting")
    os.remove(PID_FILE_PATH)
    exit(0)

sources = { }

count = 0

for log in log_file:
    dic = {'raw': log}
    normalizer.normalize(dic)
    if dic.get('date')==None:
        continue
    dic['date']=dic['date'].replace(year=datetime.datetime.today().year)
    if dic.get('date') < mindate:
        continue
    if dic.get('date') == mindate:
        if session.query(Event).filter(
                                Event.date == mindate).filter(
                                Event.action == dic.get('action')).filter(
                                Event.user == dic.get('user')).filter(
                                Event.program == dic.get('program')).count() > 0 : 
            continue
    if dic.get('program') == 'sshd':
        # Gestione connessioni ssh: il source ip si trova su una action
        # 'accepted', mentre la connessione viene aperta in 'open'
        if dic.get('action')=='accept':
            sources[dic.get('user')] = dic.get('source_ip')
        if dic.get('action')=='open':
            session.add(Event(    dic['date'],
                                dic.get('action'),
                                dic.get('user'),
                                dic.get('program'),
                                dic.get('source'),
                                sources.get(dic.get('user'))
                            ))
            count=count+1
        if dic.get('action') == 'close' :
            session.add(Event(    dic['date'],
                                dic.get('action'),
                                dic.get('user'),
                                dic.get('program'),
                                dic.get('source'),
                                ''
                            ))
            count=count+1
    elif dic.get('program') == 'cron':
        # Non ci interessano le azioni di cron
        continue
    else:
        # Non arriva da sshd ne da cron
        if dic.get('action')=='open' or dic.get('action')=='close' :
            session.add(Event(    dic['date'],
                                dic.get('action'),
                                dic.get('user'),
                                dic.get('program'),
                                dic.get('source'),
                                ''
                            ))
            count=count+1
debugMessage(2, "ho trovato "+str(count)+" nuovi eventi")
session.commit()
debugMessage(3,"session committed")
log_file.close()
debugMessage(3,"debug file closed")
os.remove(PID_FILE_PATH)
debugMessage(3,"pid file removed")
