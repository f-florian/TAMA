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
import ConfigParser

TAMA_CONFIG_FILE = "/etc/tama/tama.ini"

tama_config = ConfigParser.ConfigParser()
tama_config.read(TAMA_CONFIG_FILE)
try:
    debug = tama_config.getint("default","debug")
    ethers_format = tama_config.get("tamaetc","ethers_format")
    ethers_target = tama_config.get("tamaetc","ethers_target")
    if tama_config.has_option("tamaetc","ethers_head"):
        ethers_head = tama_config.get("tamaetc","ethers_head")
    else:
        ethers_head = None

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

if options.ethers or options.all:
    if ethers_head is not None:
        ethers_head_file = open(ethers_head,"r")
        ethers = ethers_head_file.read()
        ethers += "\n"
    else:
        ethers = ""
    for client in tama.session.query(tama.Client):
        ethers+=(ethers_format.format(name=client.name,ip=client.ip,mac=client.mac)+"\n")
    ok = not options.simulate
    if not options.quiet:
        print "This is the ethers file:"
        print ethers
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
            ethers_target_file = open(ethers_target,"w")
            ethers_target_file.write(ethers)
            print "ethers file writed"
    
