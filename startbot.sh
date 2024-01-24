#!/usr/bin/env bash
# This file can be called repeatedly from crontab to ensure the bot stays running 

BOTDIR=/home/dylix/scripts/genmaybot

PID=$(pgrep -f "/usr/bin/SCREEN -S snoonet -d -m /usr/bin/python3 genmaybot.py")
if [ -z $PID ]; then
        echo "Bot not found running, starting..."
        cd $BOTDIR
        /usr/bin/screen -S snoonet -d -m /usr/bin/python3 genmaybot.py
else
        echo "Bot already running."
fi
