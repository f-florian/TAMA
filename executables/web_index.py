#!/usr/bin/python
# -*- coding: utf-8 -*-

# web_index.py
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

TAMA_CONFIG_FILE = "/etc/tama/tama.ini"

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

def state_integer_to_color(state_number):
    """
    Convert a state number to a color combination (background, text)
    
    There are an additional status for swithced on client with user
    connected

    """
    if state_number==0:   # morto
        # White text on Black background
        return ("#000000","#FFFFFF")
    elif state_number==1:   # spento, accenzione remota non funzionante
        # White text on DarkRed background
        return ("#8B0000","#FFFFFF")
    elif state_number==2:   # spento (non da tamaserver)
        # White text on Red background
        return ("#FF0000","#FFFFFF")
    elif state_number==3:   # spento da tamaserver
        # White text on OrangeRed background
        return ("#FF4500","#FFFFFF")
    elif state_number==4:   # non gestito da tamaserver
        # Black text on White background
        return ("#FFFFFF","#000000")
    elif state_number==5:   # acceso, tamaclient non funzionante
        # Black text on Yellow background
        return ("#FFFF00","#000000")
    elif state_number==7:   # acceso, nessun utente connesso
        # Black text on Green background
        return ("#008000","#000000")
    elif state_number==8:   # acceso, utenti connessi
        # Black text on DarkGreen background
        return ("#006400","#000000")
    else:
        raise Exception("Unknown state code")

        

def generate_client_box(x,y):
    """
    Generate the informations of the client in position x,y
    
    This function generate the box for the diagram table
    
    """
    query = tama.session.query(tama.Client)\
                        .filter(tama.Client.pos_x==x)\
                        .filter(tama.Client.pos_y==y)
    if query.count()==0:
        name = " "
        background_color = "#FFFFFF"
        text_color = "#FFFFFF"
    elif query.count()==1:
        client = query.one()
        name = client.name
        if client.state==7 and client.users>0:
            (background_color,text_color) = state_integer_to_color(8)
        else:
            (background_color,text_color) = state_integer_to_color(client.state)
    else:
        name = "Internal error!"
        background_color = "#0000FF"
        text_color = "#FFFFFF"
    output = ""
    output += "   <td width=\"200\" height=\"50\" align=\"center\" bgcolor=\""+background_color+"\">\n"
    output += "    <font color=\""+text_color+"\">\n"
    output += "     "+name+"\n"
    output += "    </font>\n"
    output += "   </td>\n"
    return output

def generate_diagram():
    """
    Generate the diagram of the clients
    
    """
    output = ""
    output += " <h2 align=\"center\">Computer diagram</h2>\n"
    output += " <table align=\"center\">\n"
    max_x = tama.max_x() + 1
    max_y = tama.max_y() + 1
    for i in reversed(range(max_y)):
        output += "  <tr>\n"
        for j in range(max_x):
            output += generate_client_box(j,i)
        output += "  </tr>\n"
    output += " </table>\n"
    return output

def generate_table():
    """
    Generate a table whith data from all client
    
    """
    output = ""
    output += " <h2 align=\"center\">Computer list</h2\n>"
    output += " <table border=\"1\">\n"
    output += "  <tr>"
    output += "   <th>ID</th>"
    output += "   <th>Name</th>"
    output += "   <th>IP address</th>"
    output += "   <th>MAC address</th>"
    output += "   <th>Users</th>"
    output += "   <th>State</th>"
    output += "   <th>Last on</th>"
    output += "   <th>Last off</th>"
    output += "   <th>Last busy</th>"
    output += "   <th>Last refresh</th>"
    output += "   <th>Memory</th>"
    output += "  </tr>"    
    for client in tama.session.query(tama.Client):
        output += "  <tr>"
        output += "   <td>"+str(client.id)+"</td>"
        output += "   <td>"+client.name+"</td>"
        output += "   <td>"+client.ip+"</td>"
        output += "   <td>"+client.mac+"</td>"
        output += "   <td>"+str(client.users_human())+"</td>"
        output += "   <td>"+client.str_state()+"</td>"
        output += "   <td>"+str(client.last_on)+"</td>"
        output += "   <td>"+str(client.last_off)+"</td>"
        output += "   <td>"+str(client.last_busy)+"</td>"
        output += "   <td>"+str(client.last_refresh)+"</td>"
        output += "   <td>"+str(client.memory)+"</td>"
        output += "  </tr>"
    output += " </table>"
    return output


def generate_body():

    """
    Generate the body of the html document
    
    """
    output = ""
    output += "<body>\n"
    output += " <h1 align=\"center\">TAMA master system diplay</h1>\n"
    output += generate_diagram()
    output += generate_table()
    output += ""
    output += ""
    output += "</body>\n"
    return output
    

def main():
    output_file = open(index_target,"w")
    output_file.write("<html>\n")
    output_file.write(generate_header("TAMA - master systems display"))
    output_file.write(generate_body())
    output_file.write("</html>\n")
    output_file.close()
    
main()
