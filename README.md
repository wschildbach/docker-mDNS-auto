# A docker mDNS publisher

docker-mdns-publisher is a daemon designed to work with docker, best used with `docker compose`.

It sits in the background, waiting for containers that are started. If the containers expose
a specific label, then the daemon interprets the label as a local hostname and registers it
with the avahi daemon.

This makes it very convenient to run docker containers that expose services to the local
network, using .local domain labels to access them.

The container
can run the avahi daemon internally, such that it does not need to be installed
on the host. This also obviates the need to give the container access
to the D-Bus.

## Deploying

Create an empty directory, and create a compose.yml file:

```yaml
services:
  docker-mdns-publisher:
    image: ghcr.io/wschildbach/docker-mdns-publisher:1.0
    build: .
    read_only: true
    network_mode: host
    tmpfs: # provide a temp mount for the dbus socket, and for avahi
      - /run/dbus
      - /run/avahi-daemon
    restart: on-failure:10
    environment:
      - LOG_LEVEL=INFO # INFO is the default
      - PYTHONUNBUFFERED=1
    volumes:
      # map the docker socket to be able to monitor container lifecycles
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./avahi/avahi-daemon.conf:/etc/avahi/avahi-daemon.conf:ro
```

Then issue `docker compose up -d`, and/or make sure that whenever your system starts up, this service gets started too.
Details depend on your distribution.

When the daemon starts up, expect to see something like

```
docker-mdns-publisher-1  | INFO:docker-mdns-publisher:docker-mdns-publisher daemon v**** starting.
```

...in the log. Depending on whether any services are running which are configured to be registered, you will also see lines such as

```
docker-mdns-publisher-1  | INFO:docker-mdns-publisher:publishing test1.local
```

### Configuration

The daemon is configured through environment variables.

**TTL**
> This sets the TTL for the mDNS publication, in seconds. The default is 120 seconds.
When other machines on the network resolve `.local` domain addresses through mdns,
they can cache the result for up to TTL seconds, after which they have to do another
mdns request. This also means that mdns mappings can persist for some time after the
container has been stopped.

**LOG_LEVEL**
> This sets the verbosity of logging. Use the [log levels of the python logging module](https://docs.python.org/3/library/logging.html#logging-levels)
(CRITICAL, ERROR, WARNING, INFO, DEBUG). The default is INFO.

**DISABLE_AVAHI**
> This disables the internal avahi daemon. In this case, an avahi daemon
needs to run on the host. Be sure to also give the container access to the D-Bus
such that it can talk to the hosts avahi daemon.

**EXTRA_PROBING**
> Normally, the daemon checks whether a given cname is already published and warns or errors if it is.
This makes operation more robust but adds a lot of delay to publication. Setting EXTRA_PROBING to "no"
disables the additional check.

## Publishing an mdns record for your service

In your service compose file definition, add a label `mdns.publish=myhost.local` and restart your
service/container (replace `myhost` with whatever DNS name you want to give your service). The
daemon then publishes `myhost.local` through avahi, using the local interface adresses.

More than one comma-separated names can be given in the label.

When the container is stopped, the host is unpublished. Depending on the TTL, it may take some
seconds to minutes until the change becomes effective.

If you are using traefik, then more than one service can be hosted behind the same port.

Obviously, you could also supply labels in the Dockerfile of your service, or on the command line, if that is more convenient.

### Example

```yaml
services:
  test:
    image: alpine
    command: "sleep 15"
    labels:
      - mdns.publish=test1.local
```

## Development and debugging

To enable debugging on the daemon, set the `LOG_LEVEL` environment variable.
`LOG_LEVEL` must be set to one of the [standard python log levels](https://docs.python.org/3/library/logging.html#logging-levels).
You can set this in the compose.yml file:

```yaml
    environment:
      - LOG_LEVEL=DEBUG
```

The compose.yml file provides a few test services which register themselves. Start the daemon using
`docker compose --profile debug up` and the test services will start up together with the daemon.
The test services simply wait for a predetermined time, then terminate.

## Credits

The project took inspiration from [github/hardillb/traefik-avahi-helper](https://github.com/hardillb/traefik-avahi-helper)
which in turn borrows from [github/alticelabs/mdns-publisher](https://github.com/alticelabs/mdns-publisher).

Many thanks to [Andreas Schildbach](https://github.com/schildbach) for feedback and suggestions to this project.
