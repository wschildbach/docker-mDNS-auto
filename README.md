# docker-mDNS-auto

docker-mDNS-auto is a dameon designed to work with docker, best used with docker compose.

It sits in the background, waiting for containers that are started. If the containers expose
a specific label, then the daemon interprets the label as a local hostname and registers it
with the avahi daemon.

This makes it very convenient to run docker containers that expose servies to the local
network, using .local domain labels to access them.

## Using

In your compose file definition, add a label "mDNS.publish=myhost.local". The daemon then
publishes myhost.local using the local IP adress. Several comma-separated names can be
given in the label,

## Setting the daemon up

docker compose up docker-mDNS-auto
