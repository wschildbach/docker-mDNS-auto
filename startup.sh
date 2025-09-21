#!/bin/bash

_term() { 
  echo "Caught SIGTERM signal! In BASH" 
  kill -TERM "$pid_avahi" 2>/dev/null # kill the avahi
  sleep 1
  kill -TERM "$pid_dbus" 2>/dev/null # kill the avahi
}

echo Starting D-BUS
/usr/bin/dbus-daemon --fork --nopidfile --nosyslog --print-address=1 --system >/tmp/ad
pid_dbus=$!
sleep 1

DBUS_SESSION_BUS_ADDRESS=$(cat /tmp/ad)

echo DBUS=$DBUS_SESSION_BUS_ADDRESS

echo Starting avahi
/sbin/avahi-daemon &
pid_avahi=$!


trap _term SIGTERM

/helper/bin/python3 /helper/dockersock_watcher.py

#wait "$child"
