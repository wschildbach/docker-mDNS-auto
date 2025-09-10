# docker-mDNS-auto

docker-mDNS-auto is a daemon designed to work with docker, best used with `docker compose`.

It sits in the background, waiting for containers that are started. If the containers expose
a specific label, then the daemon interprets the label as a local hostname and registers it
with the avahi daemon.

This makes it very convenient to run docker containers that expose servies to the local
network, using .local domain labels to access them.

## Deploying

`docker compose up`

## Using with your services

In your service compose file definition, add a label "mDNS.publish=myhost.local" and restart your
service/container. The daemon then publishes myhost.local using the local IP adress. If necessary,
more than one comma-separated names can be given in the label.

## Development and debugging

To enable debugging on the daemon, set the `LOG_LEVEL` environment variable.
`LOG_LEVEL` must be set to one of the [standard python log levels](https://docs.python.org/3/library/logging.html#logging-levels).
You can set this in the compose.yml file:

```
    environment:
      - LOG_LEVEL=DEBUG
```

The compose.yml file provides a few test services which register themselves. Start the daemon using
`docker compose --profile debug up` and the test services will start up together with the daemon.
