FROM python:3-slim AS build-stage

ENV DEBIAN_FRONTEND noninteractive
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
          --mount=target=/var/cache/apt,type=cache,sharing=locked \
          rm -f /etc/apt/apt.conf.d/docker-clean && \
          apt-get update && \
          apt-get --yes upgrade && \
          apt-get --yes install build-essential python3 libdbus-glib-1-dev pip && \
          apt-get --yes install pkg-config cmake python3-venv

# during build, no need to run as user
RUN adduser --disabled-password --disabled-login --home /helper --shell /bin/false --quiet helper 1>/dev/null 2>/dev/null
USER helper

RUN python3 -m venv /helper && \
          /helper/bin/pip install --upgrade pip && \
          /helper/bin/pip install docker && \
          /helper/bin/pip install dbus-python && \
          /helper/bin/pip install mdns-publisher

COPY dockersock_watcher.py /helper

# in the runner stage, we have to run as root unfortunately, for access to the docker socket and to dbus
FROM python:3-slim AS runner

LABEL org.opencontainers.image.source=https://github.com/wschildbach/docker-mdns-publisher
LABEL org.opencontainers.image.description="listens to docker socket and picks up host.local names from compose labels, publishing them with avahi"
LABEL org.opencontainers.image.licenses=GPL-3.0-or-later

ENV DEBIAN_FRONTEND noninteractive
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
          --mount=target=/var/cache/apt,type=cache,sharing=locked \
          rm -f /etc/apt/apt.conf.d/docker-clean && \
          apt-get update && \
          apt-get --yes upgrade && \
	  apt-get --yes install python3-avahi python3-docker

RUN mkdir /helper
COPY --from=build-stage /helper /helper

CMD /helper/bin/python3 /helper/dockersock_watcher.py
