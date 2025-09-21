#!/bin/bash

terminate() { 
  echo "Caught SIGTERM signal! In BASH" 
  kill -TERM "$pid_avahi" 2>/dev/null # kill the avahi
  sleep 1
  kill -TERM "$pid_dbus" 2>/dev/null # kill the dbus
}

echo Starting D-BUS
/usr/bin/dbus-daemon --fork --nopidfile --nosyslog --system
pid_dbus=$!

echo Starting avahi
/sbin/avahi-daemon &
pid_avahi=$!

trap terminate SIGTERM

/helper/bin/python3 /helper/dockersock_watcher.py
