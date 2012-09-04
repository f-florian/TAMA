#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This module provides some common feature for programs that have to be
run on server

It provides:
 - definition of common classes and integration with sqlalchemy
 - function to refresh database data
 - functions to switch on or off clients
 - functions 
 - some stupid function to query the database

"""

# tamascommon.py
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

# In this file there is some classes used by tamaserver
# It also start the sqlalchemy engine (and session?)

import os
import sqlalchemy
import sqlalchemy.ext
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import thread
import socket
#import signal
import subprocess
import datetime
import time
import ConfigParser

TAMA_CONFIG_FILE = "/etc/tama/tama.ini"

_debug = 0
#MAIN_DB_PATH = "main.db"
#TAMA_DIR = "/afs/uz.sns.it/user/enrico/private/tama/"

def debug_message (level, msg):
    if level <=_debug:
        print "[Tamascommon - debug] "+str(msg)


debug_message(4,"parsing "+TAMA_CONFIG_FILE)
tama_config = ConfigParser.ConfigParser()
tama_config.read(TAMA_CONFIG_FILE)
try:
    _debug = tama_config.getint("default","debug")
    tama_dir = tama_config.get("default","tama_dir")
    main_db_path = tama_config.get("tamascommon","main_db_path")
    eth_interface = tama_config.get("tamascommon","eth_interface")
except:
    print "[tamascommon] error while parsing "+TAMA_CONFIG_FILE
    print "[tamascommon] exiting..."
    exit(2)
    



engine = sqlalchemy.create_engine('sqlite:///'+main_db_path)
Base = sqlalchemy.ext.declarative.declarative_base()

class Client(Base):
    """
    Save informations about one client
    
    Attributes:
        id          The primary key for database
        name        The name of the client
        ip          The ip address of the client
        mac         The mac address of the client
        users       The number of users connected to the client
        state       The state of the client (numerical aliases)
                        0: morto (manuale)
                        1: spento, accensione remota non funzionante
                        2: spento (non da tamaserver)
                        3: spento da tamaserver
                        4: non gestito da tamaserver
                        5: acceso, tamaclient non funzionante
                        7: acceso
        auto_on     Can the client be switched on automatically?
        auto_off    Can the client be switched off automatically?
        always_on   Have the client to be always on?
        count       Add this client to the list of free clients
        last_on     The last time that the client was see online
        last_off    The last time that the client was see offline
        pos_x       Position of the client in the room, x coordinate
        pos_y       Position of the client in the room, y coordinate
    

        
    """
    __tablename__ = 'clients'
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True) 
    """The primary key for database"""
    
    name = sqlalchemy.Column(sqlalchemy.String)
    """The name of the client"""
    
    ip = sqlalchemy.Column(sqlalchemy.String)
    """The ip address of the client"""
    
    mac = sqlalchemy.Column(sqlalchemy.String)
    """The mac address of the client"""
    
    users = sqlalchemy.Column(sqlalchemy.Integer)
    """The number of users connected to the client"""
    
    state = sqlalchemy.Column(sqlalchemy.Integer)
    """The state of the client (numerical aliases)"""
    
    auto_on = sqlalchemy.Column(sqlalchemy.Boolean)
    """Can the client be switched on automatically?"""
    
    auto_off = sqlalchemy.Column(sqlalchemy.Boolean)
    """Can the client be switched off automatically?"""
    
    always_on = sqlalchemy.Column(sqlalchemy.Boolean)
    """Have the client to be always on?"""
    
    count = sqlalchemy.Column(sqlalchemy.Boolean)
    """Add this client to the list of free clients"""
    
    last_on = sqlalchemy.Column(sqlalchemy.DateTime)
    """The last time that the client was see online"""
    
    last_off = sqlalchemy.Column(sqlalchemy.DateTime)
    """The last time that the client was see offline"""
    
    pos_x = sqlalchemy.Column(sqlalchemy.Integer)
    """Position of the client in the room, x coordinate"""
    
    pos_y = sqlalchemy.Column(sqlalchemy.Integer)
    """Position of the client in the room, y coordinate"""
    
    
    def __init__ (self, name, ip, mac, state, auto_on, auto_off, always_on, count):

        self.name = name
        self.ip = ip
        self.mac = mac
        if state < 4:
            self.users = -2
        else:
            self.users = -1
        self.state = state
        self.auto_on = auto_on
        self.auto_off = auto_off
        self.always_on = always_on
        self.count = count
        self.last_on = datetime.datetime.now()
        self.last_off = datetime.datetime.now()
    
    def __repr__(self):
        return "<Client(name: '%s', ip: '%s', mac: '%s',users: %d, state: %d, auto_on: %s, auto_off: %s, always_on: %s, count: %s, last_on: %s, last_off: %s)>" % (
                                            self.name,
                                            self.ip,
                                            self.mac,
                                            self.users,
                                            self.state,
                                            self.auto_on,
                                            self.auto_off,
                                            self.always_on,
                                            self.count,
                                            str(self.last_on),
                                            str(self.last_off)
                                            )
    
    def ping (self):
        """
        Ping client and return True if it is online
        
        Keyword arguments:
        address -- the address (ip or name) to probe
        
        """
        (stdout, stderr) = subprocess.Popen(["ping","-c 1","-w 1",str(self.ip)], stdout=subprocess.PIPE).communicate()
        lines = stdout.splitlines()
        for line in lines:
            if "1 received" in line:
                return True
        return False
        
        
    def is_online(self):
        """
        Check if the client is online
        
        """
        return self.ping()
    
    def refresh(self):
        """
        Refresh all information about this client and add a new
        temperature measure
        
        """
        debug_message(3, "Refreshing client "+self.name)
        online = self.is_online()
        if (not online) and self.state > 4:
            # the first time offline
            self.state = 2
            self.users = -2
            self.last_off = datetime.datetime.now()
        if (not online):
            debug_message(3,"Client "+self.name+" not online")
            session.commit()
            return
        
        if online:
            if self.state < 5:
                # the first time online
                self.last_on = datetime.datetime.now()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.ip, 100))
        except:
            self.state = 5
            self.user = -1
            debug_message(2,self.name+": tama not responding")
            return
        else:
            self.state = 7
            time.sleep(1)
            s.settimeout(10)
            try:
                s.send("connected")
                self.users = int(s.recv(1024).rstrip("\n"))
            except:
                self.state = 5
                self.user = -1
                debug_message(2,self.name+": tama not responding")
                session.commit()
                return
            try:
                s.send("temp0")
                temp = float(s.recv(1024).rstrip().rstrip("°C\n"))
            except:
                self.state = 5
                self.user = -1
                debug_message(2,self.name+": tama not responding")
                session.commit()
                return
            self.temperatures.append(Temperature(datetime.datetime.now(),temp))
            s.send("quit")
            s.close()
            session.commit()
    
    def switch_on_simple(self):
        """
        Send a wakeonlan magic packet to the client and exit
        
        """
        debug_message(2,"Accendo "+self.name)
        os.system(TAMA_DIR+"tamason.sh "+self.mac+" "+eth_interface)
        
    
    def switch_on(self):
        """
        Try to switch on target
        
        Keyword arguments:
        target -- the object related to the client to switch on
        
        Note:
        the execution of this function requires from 1 to 2 minutes, so I 
        encourage you to execute this function in multi-threading
        
        """
        Session = sqlalchemy.orm.sessionmaker(bind=engine)
        session = Session()
        self.switch_on_simple()
        time.sleep(60)              # wait to power on
        online = self.is_online()
        if online:
            self.state=7
            self.last_on=datetime.datetime.now()
            session.commit()
            session.close()
            return True
        else:
            debug_message(2,"Riprovo l'accensione di "+self.name)
            self.switch_on_simple()
            time.sleep(60)
            online = self.is_online()
            if online:
                self.state=7
                self.last_on=datetime.datetime.now()
                session.commit()
                session.close()
                return True
            else:
                debug_message(2,"Non riesco ad accedere "+self.name)
                self.state = 1
                session.commit()
                session.close()
                return False
    
    
    def switch_on_multithreading(self):
        """
        This function is a multithreading implementation if switch_on
        
        """
        try:
            thread.start_new_thread(self.switch_on,())
        except:
            debug_message(1, "Unable to start a new thread!")
        
    
    def switch_off(self):
        """
        Try to switch on target
        
        Keyword arguments:
        target -- the object related to the client to switch on
        
        """
        debug_message(2,"Switching off client "+self.name)
        os.system("ssh "+self.ip+" shutdown -h now")
        self.state = 3
        self.users = -2
        self.last_off = datetime.datetime.now()
        session.commit()
    
    def switch(self,state):
        """
        True: switch on
        False: switch off
        
        """
        if state == True:
            self.switch_on()
        else:
            self.switch_off()
        
    def str_state(self):
        """
        Return explicit string version of the client state
        
        """
        if self.state==0:
            return "Morto"
        elif self.state==1:
            return "Spento, accensione remota non funzionante"
        elif self.state==2:
            return "Spento (non da tamaserver)"
        elif self.state==3:
            return "Spento da tamaserver"
        elif self.state==4:
            return "Non gestito da tamaserver"
        elif self.state==5:
            return "Acceso, tamaclient non funzionante"
        elif self.state==7:
            return "Acceso"
        else:
            return "Stato non riconosciuto"
    
    def users_human(self):
        if self.users > 0:
            return self.users
        else:
            return 0
            
    def delete(self):
        """
        Delelte all informations about this client and the client itself
        
        """
        debug_message(4,"Deleting all temperatures about "+self.name)
        for temperature in self.temperatures:
            session.delete(temperature)
        debug_message(4,"Deleting all auth events about "+self.name)
        for event in self.authEvents:
            session.delete(event)
        debug_message(4,"Deleting client "+self.name)
        session.delete(self)
        session.commit()
        
    def consistency_check_users(self, correct=False):
        """
        Check for all clients if the number of user reported in consistent
        whith the client state
        
        """
        if self.state <= 3:
            if self.users != -2:
                if correct:
                    debug_message(1,"Correcting the number of users in client "+self.name)
                    self.users = -2
                else:
                    raise Exception("Found inconsistency in user number of client "+client.name)
        elif self.state <=5:
            if self.users != -1:
                if correct:
                    debug_message(1,"Correcting the number of users in client "+self.name)
                    self.users = -1
                else:
                    raise Exception("Found inconsistency in user number of client "+client.name)
        
    def consistency_check_always_on(self, correct=False):
        """
        If always_in is true then check if auto_on is true and
        auto_off is false
        
        """
        if self.always_on:
            if not auto_on:
                if correct:
                    debug_message(1,"Correcting auto_on in client "+client.name)
                    self.auto_on = True
                else:
                    raise Exception("Auto_on is false in always on client "+client.name)
            if auto_off:
                if correct:
                    debug_message(1,"Correcting auto_off in client "+client.name)
                    self.auto_off = False
                else:
                    raise Exception("Auto_off is true in always on client "+client.name)
        
                                
        
class AuthEvent(Base):
    """
    Save information about auth event (connection and disconenction of
    users)
    
    """
    __tablename__ = 'auth_events'
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    """The primary key for database"""
    
    local_id = sqlalchemy.Column(sqlalchemy.Integer)
    """The id in the local database store in the client"""
    
    date = sqlalchemy.Column(sqlalchemy.DateTime)
    """When event appen"""
    
    action = sqlalchemy.Column(sqlalchemy.String)
    """What appen"""
    
    user = sqlalchemy.Column(sqlalchemy.String)
    """The user that do it"""
    
    program = sqlalchemy.Column(sqlalchemy.String)
    """The program that do it"""
    
    source = sqlalchemy.Column(sqlalchemy.String)
    """The source of auth.log (aka the client name)"""
    
    source_ip = sqlalchemy.Column(sqlalchemy.String)
    """The source ip of connection (only for sshd)"""
    
    client_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('clients.id'))
    """The client id according the clients table"""
    
    client = sqlalchemy.orm.relationship("Client",
                            backref = sqlalchemy.orm.backref('authEvents',
                                order_by=id))
    """Relationship with clients table"""
    
    def __init__ (self, local_id, date, action, user, program, source, source_ip):
        self.local_id = local_id
        self.date = date
        self.action = action
        self.user = user
        self.program = program
        self.source = source
        self.source_ip = source_ip
    

class Temperature(Base):
    """
    One temperature reading for a client
    
    """
    __tablename__ = 'temperatures'
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    """The primary key for database"""
    
    date = sqlalchemy.Column(sqlalchemy.DateTime)
    """The date of measure"""
    
    measure = sqlalchemy.Column(sqlalchemy.Float)
    """The temperature measured"""
    
    client_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('clients.id'))
    """The client id according the clients table"""
    
    client = sqlalchemy.orm.relationship("Client",
                            backref = sqlalchemy.orm.backref('temperatures',
                                order_by=id))
    """Relationship with clients table"""
    
    def __init__ (self, date, measure):
        self.date = date
        self.measure = measure
    
    def __repr__(self):
        return "<Temperature('%s','%s','%s C')>" % (self.client.name,
                                                    str(self.date),
                                                    str(self.measure))
    

Base.metadata.create_all(engine) 
Session = sqlalchemy.orm.sessionmaker(bind=engine)
session = Session()


def refresh_data():
    """
    Refresh data in the main database.
    
    This function refresh the state of all client and add a new measure
    to the "temeperatures" table
    
    """
    for client in session.query(Client).filter(Client.state != 0).filter(Client.state != 4):
        client.refresh()
        
    session.commit()

# Funzioni per convalidare o convertire le stringhe

def string_to_bool(string):
    """
    Convert a string (True/False) in a boolean value
    
    """
    string = string.lower().strip()
    if string in [ "true", "1", "yes", "y", "t" ]:
        return True
    elif string in [ "false", "0", "no", "n", "f" ]:
        return False
    else:
        raise Exception ("Invalid bool string")

def validate_ip(string):
    """
    Return string if string is a IP, else raise an exception
    
    """
    ip = string.split(".")
    if len(ip)!=4:
        raise Exception("Invalid IP")
    for i in range(4):
        try:
            num = int(ip[i])
        except:
            raise Exception("Invalid IP")
        else:
            if num<0 or num>255:
                raise Exception("Invalid IP")
    return string

def validate_mac(string):
    """
    Return string if string is a MAC address, else raise an exception
    
    """
    mac = string.split(":")
    if len(mac)!=6:
        raise Exception("Invalid MAC address")
    for i in range(6):
        try:
            num = int(mac[i],16)
        except:
            raise Exception("Invalid MAC address")
        else:
            if num<0 or num>255:
                raise Exception("Invalid MAC address")
    return string

    

# Funzioni stupide
def query_name(name):
    """
    This function returns the object associated to the client
    
    Keywords arguments:
    name -- the name of the client
    
    """
    try:
        client = session.query(Client).filter(Client.name==name).one()
    except:
        debug_message(1,"Client "+str(name)+" not found in database")
        return None
    else:
        return client
    

#~ def query_temperature_name(name):
    #~ """
    #~ This function returns the temperatures recorded in the client
    #~ 
    #~ Keywords arguments:
    #~ name -- the name of the client
    #~ 
    #~ """
    #~ try:
        #~ temperatures = session.query(Temperature).filter(
                    #~ Temperature.client.name==name).order_by(
                    #~ Temperature.date).all()
    #~ except:
        #~ debug_message(1,"Error while getting temperatures for client "+
                    #~ str(name)+" in the database")
    #~ else:
        #~ return temperatures
    #~ 

def max_x():
    """
    Returns the maximum x coordinate of all clients
    
    """
    return session.query(sqlalchemy.func.max(Client.pos_x))

def max_y():
    """
    Returns the maximum y coordinate of all clients
    
    """
    return session.query(sqlalchemy.func.max(Client.pos_y))




def db_consistency_check_positions():
    """
    Check if there are two (or more) clients in the same position
    
    """
    mem = []
    for x,y in session.query(Client.pos_x, Client.pos_y):
        debug_message(3,"Read position "+str(x)+","+str(y))
        if x == -1:
            continue
        else:
            if (x,y) in mem:
                debug_message(1,"Problem in position "+str(x)+","+str(y))                                 
                raise Exception("Two clients are in the same position!")
            else:
                mem.append((x,y))
    

def db_consistency_check_ip():
    """
    Check if there are two (or more) client whith the same ip address.
    Also check if all IP are valid
    
    """
    mem = []
    for ip in session.query(Client.ip):
        debug_message(3,"Read IP "+ip)
        validate_ip(ip)
        if ip in mem:
            debug_message(1,"IP "+ip+" duplicated!")
            raise Exception("Two clients have the same IP!")
        else:
            mem.append(ip)
    
def db_consistency_check_mac():
    """
    Check if there are two (or more) client whith the same mac address.
    Also check if all mac are valid
    
    """
    mem = []
    for mac in session.query(Client.mac):
        debug_message(3,"Read MAC "+mac)
        validate_mac(mac)
        if mac in mem:
            debug_message(1,"MAC "+mac+" duplicated!")
            raise Exception("Two clients have the same MAC!")
        else:
            mem.append(mac)

def db_consistency_check_users(correct=False):
    """
    Check for all clients if the number of user reported in consistent
    with the client state
    
    """
    for client in session.query(Client):
        client.consistency_check_users(correct)
    
def db_consistency_check_always_on(correct=False):
    """
    Check for all client with always_on if auto_on is true and aut_off
    is false
    
    """
    for client in session.query(Client).filter(Client.always_on == True):
        client.consistency_check_always_on(correct)
    

def diagnostics(level=3):
    """
    Run a diagnostic on tamaserver.
    
    Tama will run every diagnostic whith level less or equal of level
    
    level 1:
    level 2:
    level 3:
    level 4:
    level 5:
    
    """
    debug_message(4,"Initializing level "+level+" diagnostic")
    try:
        int(level)
    except:
        raise Exception("Diagnostics level must be an integer!")
    else:
        if level<1 or level>5:
            raise Exception("Diagnostics level must be in 1..5!")
    if level >= 5:
        db_consistency_check_ip()
        db_consistency_check_mac()
    if level >= 4:
        db_consistency_check_positions()
    if level >= 3:
        db_consistency_check_always_on()
        db_consistency_check_users()
    if level >= 2:
        pass
    if level == 1:
        pass
    
