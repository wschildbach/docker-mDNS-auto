#!/bin/bash

_term() { 
  echo "Caught SIGTERM signal! In BASH" 
  kill -TERM "$pid_avahi" 2>/dev/null # kill the avahi
  sleep 1
  kill -TERM "$pid_dbus" 2>/dev/null # kill the avahi
}

echo Starting D-BUS
echo /usr/bin/dbus-daemon  --address=unix:path=/run/dbus/dbus_foo --nofork --nopidfile --nosyslog --print-address
/usr/bin/dbus-daemon --nofork --nopidfile --nosyslog --print-address --session
pid_dbus=$!
echo Starting avahi
#/sbin/avahi-daemon &
pid_avahi=$!

#DBUS_SESSION_BUS_ADDRESS

trap _term SIGTERM

#/helper/bin/python3 /helper/dockersock_watcher.py

#wait "$child"
