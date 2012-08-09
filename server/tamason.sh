#!/bin/bash

#echo "[tamason] Accendo $1 sull'interfaccia $2"

etherwake $1 -D -i $2
