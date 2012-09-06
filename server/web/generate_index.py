#!/usr/bin/python
# -*- coding: utf-8 -*-

# generate_index.py
# This file is part of TAMA
# 
# Copyright (C) 2012 - Enrico Polesel
# 
# TAMA is free software; you can redistribute it and/or modify
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
# along with TAMA. If not, see <http://www.gnu.org/licenses/>.

#~ import os
#~ import thread
#~ import socket
#~ import signal
#~ import subprocess
import datetime
#~ import time
#~ import sqlalchemy
#~ import sqlalchemy.orm
import ConfigParser
# import argparse
# import sys

# TAMA_CONFIG_FILE = "/etc/tama/tama.ini"

tama_config = ConfigParser.ConfigParser()
tama_config.read(TAMA_CONFIG_FILE)
try:
    debug = tama_config.getint("default","debug")
    #tama_dir = tama_config.get("default","tama_dir")
    index_target = tama_config.get("tamaweb","index_target")

except:
    print "[tamaweb] error while parsing "+TAMA_CONFIG_FILE
    print "[tamaweb] exiting..."

try:
    import tamascommon as tama
except:
    print "[tamaweb] error while importing tamascommon"
    exit(2)

def debug_message (level, msg):
    if level <=debug:
        print "[tamaweb - debug] "+str(msg)
    

def generate_header(title):
    """
    Generate a html header
    
    """
    header_format = "<head>\n <title> {} </title> \n</head> \n"

    return header_format.format(title)

def generate_diagram():
    output = ""
    output = output + " <h2 align=\"center\"> Computer diagram<\h2>\n"
    output = output + " <table align=\"centre\">\n"
    max_x = tama.max_x()
    max_y = tama.max_y()
    output = output + ""
    output = output + ""
    output = output + ""



def generate_body():
    """
    Generate the body of the html document
    
    """
    output = ""
    output = output + "<body>\n"
    output = output + " <h1 align=\"center\">TAMA master system diplay</h1>\n"
    output = output + generate_diagram()
    output = output + generate_table()
    output = output + ""
    output = output + ""
    output = output + "<\body>\n"
    

def main():
    output_file = open(index_target,"w")
    output_file.write("<html>\n")
    output_file.write(generate_header("TAMA - master systems display"))
    output_file.write(generate_body())
    output_file.write("</html>\n")
    output_file.close()
    
