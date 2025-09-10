FROM debian:bookworm-slim AS build-stage

ENV DEBIAN_FRONTEND noninteractive
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
          --mount=target=/var/cache/apt,type=cache,sharing=locked \
          rm -f /etc/apt/apt.conf.d/docker-clean && \
          apt-get update && \
          apt-get --yes upgrade && \
          apt-get --yes install build-essential python3 libdbus-glib-1-dev pip && \
          apt-get --yes install pkg-config cmake python3-venv

# during build, no need to run as user
RUN adduser --disabled-password --disabled-login --home /helper --shell /bin/false --quiet helper 2>/dev/null
#USER helper

RUN python3 -m venv /helper && . /helper/bin/activate && \
          /helper/bin/pip install --upgrade pip && \
          /helper/bin/pip install docker dbus-python mdns-publisher && \
          /helper/bin/pip freeze > /helper/requirements.txt

COPY dockersock_watcher.py /helper

CMD . /helper/bin/activate && /helper/bin/python3 /helper/dockersock_watcher.py

############################################################
#FROM python:3-slim AS runner
FROM build-stage AS runner

ENV DEBIAN_FRONTEND noninteractive
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
          --mount=target=/var/cache/apt,type=cache,sharing=locked \
          rm -f /etc/apt/apt.conf.d/docker-clean && \
          apt-get update && \
	  apt-get --yes upgrade && \
          apt-get --yes install python3-avahi python3-venv

# we have to run as root unfortunately, for access to the docker socket and to dbus
#RUN mkdir /helper
#COPY --from=build-stage /helper /helper

CMD . /helper/bin/activate && /helper/bin/python3 /helper/dockersock_watcher.py
