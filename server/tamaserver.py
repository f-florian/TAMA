#!/usr/bin/python
# -*- coding: utf-8 -*-

# tamaserver.py
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
import thread
import socket
import signal
import subprocess
import datetime
import time
import sqlalchemy
import sqlalchemy.orm
import ConfigParser

TAMA_CONFIG_FILE = "/etc/tama/tama.ini"

#debug = 4
#pid_file_path = "tamaserver.pid"
#free_policy_file = "free_policy.ini"

tama_config = ConfigParser.ConfigParser()
tama_config.read(TAMA_CONFIG_FILE)
try:
    debug = tama_config.getint("default","debug")
    #tama_dir = tama_config.get("default","tama_dir")
    
    pid_file_path = tama_config.get("tamaserver","pid_file_path")
    free_policy_file = tama_config.get("tamaserver","free_policy_file")
except:
    print "[tamaserver] error while parsing "+TAMA_CONFIG_FILE
    print "[tamaserver] exiting..."
    exit(2)

try:
    import tamascommon as tama
except:
    print "[tamaserver] error while importing tamascommon"
    exit(2)

def debug_message (level, msg):
    if level <=debug:
        print "[Tamaserver - debug] "+str(msg)

def start_pid():
    if os.path.exists(pid_file_path):
        debug_message(1, "Tamaserver is already running, exiting")
        exit(0)
    else:
        pid_file = open(pid_file_path, "w")
        pid_file.write(str(os.getpid())+"\n")
        pid_file.close()
    
def stop_pid():
    os.remove(pid_file_path)
    exit(0)


class free_policy:
    start = datetime.time
    min = int
    max = int
    
    def __init__(self, start, min, max):
        self.start = start
        self.min = min
        self.max = max
    
    def __repr__(self):
        return "<free_policy('%s',%d,%d)>" % (str(self.start), self.min, self.max)
    
    def __eq__(x,y):
        return x.start == y.start and x.min == y.min and x.max == y.max
    def __cmp__(x,y):
        return x.start == y.start and x.min == y.min and x.max == y.max
    def __lt__(x,y):
        if x.start < y.start:
            return True
        elif x.start > y.start:
            return False
        elif x.min < y.min:
            return True
        elif x.min > y.min:
            return False
        else: return x.max < y.max
   

def parse_free_policy(source):
    """
    Parse the `free_policy_file` and add free_policy objects to container
    
    """
    
    debug_message(4,"parsing "+free_policy_file)
    free_config = ConfigParser.ConfigParser()
    free_config.read(source)
    container = []
    
    try:
    #if 1==1:
        for section in free_config.sections():
            debug_message(2,"parsing section "+section)
            if free_config.has_option(section, "start_hour"):
                debug_message(3,"section "+section+" has start_hour")
                hour = free_config.getint(section,"start_hour")
                if free_config.has_option(section, "start_minute"):
                    debug_message(3,"section "+section+" has start_minute")
                    minute = free_config.getint(section,"start_minute")
                else:
                    minute = 0
            else:
                hour = free_config.getint(section,"start")
                minute = 0
            #~ print datetime.time(hour,minute,0)
            #~ print free_config.getint(section,"min")
            #~ print free_config.getint(section,"max")
            container.append(free_policy(datetime.time(hour,minute,0),
                                    free_config.getint(section,"min"),
                                    free_config.getint(section,"max")))
    except:
        print "[tamaserver] error while parsing "+free_policy_file
        print "[tamaserver] exiting..."
        stop_pid()
    else:
        container.sort()
        return container
        
    



def min_free(rules, time):
    """
    The minimum number that have to be free at time
    
    """
    temp_min = -999
    for rule in rules:
        if rule.start < time:
            temp_min = rule.min
        else: break 
    if temp_min == -999:
        temp_min = rules[-1].min
    
    return temp_min


def max_free(rules, time):
    """
    The maximum  number that have to be free at time
    
    """
    temp_max = -999
    for rule in rules:
        if rule.start < time:
            temp_max = rule.max
        else: break 
    if temp_max == -999:
        temp_max = rules[-1].max
    
    return temp_max


def compute_action(rules):
    """
    Compute the number of client to switch on (if positive) or switch
    off (if negative) in this moment
    
    """
    min_ = min_free(rules, datetime.datetime.now().time())
    max_ = max_free(rules, datetime.datetime.now().time())
    free = tama.session.query(tama.Client).filter(
                            tama.Client.count==1).filter(
                            tama.Client.state==7).filter(
                            tama.Client.users==0).count()
    if free < min_:
        return min_ - free
    elif free > max_:
        return max_ - free
    else:
        return 0
    


def decrease_free_client(num):
    """
    Try to switch on num client
    
    Keyword arguments:
    num -- the number of client to switch on
    
    """
    available = tama.session.query(tama.Client).\
        filter(tama.Client.state == 7).\
        filter(tama.Client.users == 0).\
        filter(tama.Client.auto_off == 1).\
        filter(tama.Client.always_on == 0).\
        filter(tama.Client.last_busy < datetime.datetime.now()-datetime.timedelta(minutes=10)).\
        order_by(tama.Client.last_on).\
        all()
    for client in available:
        if num <= 0:
            break
        client.switch_off()
        num = num -1
    tama.session.commit()
    return num
    


def increase_free_client(num):
    """
    Try to switch on num client
    
    Keyword arguments:
    num -- the number of client to switch on
    
    """
    available = tama.session.query(tama.Client).\
        filter(sqlalchemy.or_(tama.Client.state==2,tama.Client.state==3)).\
        filter(tama.Client.auto_on==1).\
        order_by(tama.Client.last_off).\
        all()
    
    i=0
    for client in available:
        if i>=num:
            break
        debug_message(2,"Accendo "+client.name)
        client.switch_on_multithreading()
        i=i+1
    

def check_always_on():
    """
    Check the "always_on" clients. If they are offline then try to switch
    them on 
    
    """
    targets = tama.session.query(tama.Client).\
        filter(tama.Client.always_on==True).\
        filter(tama.Client.state < 4).\
        filter(tama.Client.state > 0).\
        all()
    for client in targets:
        debugMessage(2,"Turning on "+client.name+" for always_on")
        client.switch_on_multithreading()
    return len(targets)
    

def sig_exit(signum, frame):
    """
    Manage SIGTERM or SIGINT (ctrl+C) to close the program properly
    
    """
    debug_message(4, "Closing tamaserver...")
    stop_pid()

signal.signal(signal.SIGTERM,sig_exit)
signal.signal(signal.SIGINT,sig_exit)

start_pid()
rules = []
rules = parse_free_policy(free_policy_file)
debug_message(4,"Policy: "+str(rules))

while (1):
    # main loop
    tama.refresh_data()
    num = compute_action(rules)
    check_always_on()
    debug_message(2,"delta client = "+str(num))
    if num < 0:
        decrease_free_client(-num)
    elif num > 0:
        increase_free_client(num)
    time.sleep(5*60 - ( 60*(datetime.datetime.now().minute%5) + datetime.datetime.now().second + 1 ) )


