#!/usr/bin/python

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
import datetime
import tamascommon as tama
import sqlalchemy
import sqlalchemy.orm
import sys

debug = 4
def debugMessage (level, msg):
    if level <=debug:
        print "[Tamasadd - debug] "+str(msg)

if len(sys.argv) == 1:
    print "Give me a file!"
    exit(0)
else:
    FILE = sys.argv[1]

client_list = open(FILE, "r")

def myBool(string):
    if string == "True":
        return True
    else:
        return False

Session = sqlalchemy.orm.sessionmaker(bind=tama.engine)
session = Session()

for line in client_list:
    line = line.split()
    session.add(tama.Client(line[0],line[1],line[2],line[3],line[4],myBool(line[5]),myBool(line[6]),myBool(line[7]),myBool(line[8])))
    print "Client "+line[0]+" added"

session.commit()
client_list.close()
