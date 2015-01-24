#!/bin/sh

tama_db_path='/var/tama'
tama_db_file="$tama_db_path/main.db"

if [[ -e main.db ]]
    then
        mv $tama_db_path/main.db $tama_db_path/`date +main-%Y%j.db`
        cp $tama_db_path/new.db $tama_db_path/main.db
    else
        echo "error! TAMA database not found in $tama_db_path!"
fi