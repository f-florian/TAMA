#!/usr/bin/python
# -*- coding: utf-8 -*-

# tamaserver.py
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
# along with tama. If not, see <http://www.gnu.org/licenses/>.

import argparse
import sys
import os
import ConfigParser

TAMA_CONFIG_FILE = "/etc/tama/tama.ini"

tama_config = ConfigParser.ConfigParser()
tama_config.read(TAMA_CONFIG_FILE)
try:
    debug = tama_config.getint("default","debug")

except:
    print "[tamaetc] error while parsing "+TAMA_CONFIG_FILE
    print "[tamaetc] exiting..."
    exit(2)

try:
    import tamascommon as tama
except:
    print "[tamaetc] error while importing tamascommon"
    print "[tamaetc] dying..."
    exit(2)

def debug_message(level, msg):
    if level <= debug:
        print "[tamaetc - debug] "+str(msg)



parser = argparse.ArgumentParser(description="A tool to generate\
                                 some etc files")
parser.add_argument("--all","-a",
                    help="generate all the etc files that tama can generate",
                    action="store_true")
parser.add_argument("--ethers",
                    help="Generate the ethers file",
                    action="store_true")
parser.add_argument("--dsh",
                    help="Generate dsh files",
                    action="store_true")
parser.add_argument("--hosts",
                    help="Generate hosts file",
                    action="store_true")
parser.add_argument("--dhcp",
                    help="Generate a part of the dhcp config file",
                    action="store_true")
parser.add_argument("--yes","-y",
                    help="Do not ask confirmation before writing etc files",
                    action="store_true")
# parser.add_argument("--no","-n",
#                     help="Do not write etc files, only simulate output",
#                     action="store_true")
parser.add_argument("--quiet","-q",
                    help="Do not output files before writing",
                    action="store_true")
parser.add_argument("--simulate","-s",
                    help="Do not write files",
                    action="store_true")

options = parser.parse_args()

def generate(name):
    """
    Generate the file name reading configurations from tama_config
    
    format option: name_format
    head option: name_head
    tail option: name_tail
    target option: name_target    
    
    """
    name = str(name)
    try:
        format = tama_config.get("tamaetc",name+"_format")
    except:
        print "Unable to find "+name+"_format in configuration file"
        print "Exiting..."
        exit(2)
    try:
        target = tama_config.get("tamaetc",name+"_target")
    except:
        print "Unable to find "+name+"_target in configuration file"
        print "Exiting..."
        exit(2)
    if tama_config.has_option("tamaetc",name+"_head"):
        head = tama_config.get("tamaetc",name+"_head")
    else:
        head = None
    if tama_config.has_option("tamaetc",name+"_tail"):
        tail = tama_config.get("tamaetc",name+"_tail")
    else:
        tail = None

    if head is not None:
        head_file = open(head,"r")
        buffer = head_file.read()
        buffer += "\n"
    else:
        buffer = ""
    for client in tama.session.query(tama.Client):
        buffer+=(format.format(name=client.name,ip=client.ip,mac=client.mac,n="\n",o="{",c="}")+"\n")
    ok = not options.simulate
    if not options.quiet:
        print "This is the "+name+" file:"
        print buffer
        if ok and not options.yes:
            while True:
                response = raw_input("Is it ok? [y/n] ")
                try:
                    ok = tama.string_to_bool(response)
                except:
                    print "Please give a valid responce!"
                else:
                    break
    if ok:
        target_file = open(target,"w")
        target_file.write(buffer)
        print name+" file saved"

def generate_dsh():
    """
    Generate the dsh configuation files
    
    This function read all the groups in dsh_groups_path
    and add them to machines.list. Then it add the client
    in tama database in the group named dsh_group
    
    """
    # Parse the config file
    try:
        dsh_dir = tama_config.get("tamaetc","dsh_dir").rstrip("/")
    except:
        print "Unable to find dsh_dir in tama configuration file"
        sys.exit(os.EX_CONFIG)
    try:
        dsh_group = tama_config.get("tamaetc","dsh_group")
    except:
        print "Unable to find dsh_group in tama configuration file"
        sys.exit(os.EX_CONFIG)
    
    
    machines = ""
    group = ""
    for group_path in os.listdir(dsh_dir+"/group"):
        if os.path.isdir(group_path) or \
           group_path == dsh_group or \
           group_path == "all":
            continue
        else:
            group_file = open(dsh_dir+"/group/"+group_path,"r")
            for line in group_file:
                machines += line
            machines += "\n"
            group_file.close()
    for client in tama.session.query(tama.Client):
        machines +=  client.name+"\n"
        group += client.name+"\n"
    machines += "\n"
    group += "\n"

    ok = not options.simulate
    if not options.quiet:
        print "This is the machines.list file:"
        print machines
        print
        print "This is the group "+dsh_group
        print group
        if ok and not options.yes:
            while True:
                response = raw_input("Is it ok? [y/n] ")
                try:
                    ok = tama.string_to_bool(response)
                except:
                    print "Please give a valid responce!"
                else:
                    break
    if ok:
        machines_file = open(dsh_dir+"/machines.list","w")
        machines_file.write(machines)
        machines_file.close()
        print "machines.list saved"
        group_file = open(dsh_dir+"/group/"+dsh_group,"w")
        group_file.write(group)
        group_file.close()
        print dsh_group+" saved"
    
if options.ethers or options.all: 
    generate("ethers")
if options.hosts or options.all:
    generate("hosts")
if options.dhcp or options.all:
    generate("dhcp")
if options.dsh or options.all:
    generate_dsh()
    
