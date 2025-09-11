# A docker mDNS publisher

docker-mdns-publisher is a daemon designed to work with docker, best used with `docker compose`.

It sits in the background, waiting for containers that are started. If the containers expose
a specific label, then the daemon interprets the label as a local hostname and registers it
with the avahi daemon.

This makes it very convenient to run docker containers that expose services to the local
network, using .local domain labels to access them.

## Deploying

In this directory, issue `docker compose up -d`.

### Configuration

**TTL**
 > This sets the TTL for the mDNS publication, in seconds. The default is 120 seconds.

**LOG_LEVEL**
> This sets the verbosity of logging. Use the [log levels of the python logging module](https://docs.python.org/3/library/logging.html#logging-levels)
(CRITICAL, ERROR, WARNING, INFO, DEBUG).

## Using with your services

In your service compose file definition, add a label "mdns.publish=myhost.local" and restart your
service/container. The daemon then publishes myhost.local using the local IP adress. If necessary,
more than one comma-separated names can be given in the label.

When the container is stopped, the host is unpublished. Depending on the TTL, it may take some
seconds to minutes until the change becomes effective.

### Example

```
services:
  test:
    image: test
    labels:
      - mdns.publish=test1.local
```

## Development and debugging

To enable debugging on the daemon, set the `LOG_LEVEL` environment variable.
`LOG_LEVEL` must be set to one of the [standard python log levels](https://docs.python.org/3/library/logging.html#logging-levels).
You can set this in the compose.yml file:

```
    environment:
      - LOG_LEVEL=DEBUG
```

If the machine which you develop on does not have an avahi daemon, or you don't want any mDNS publication during development,
set `USE_AVAHI=NO` for the daemon.

The compose.yml file provides a few test services which register themselves. Start the daemon using
`docker compose --profile debug up` and the test services will start up together with the daemon.
The test services simply wait for a predetermined time, then terminate.
