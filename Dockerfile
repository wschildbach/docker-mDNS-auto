FROM debian:bookworm-slim AS build-stage

ENV DEBIAN_FRONTEND noninteractive
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
          --mount=target=/var/cache/apt,type=cache,sharing=locked \
          rm -f /etc/apt/apt.conf.d/docker-clean && \
          apt-get update && \
          apt-get --yes upgrade && \
          apt-get --yes install build-essential python3 libdbus-glib-1-dev pip && \
          apt-get --yes install pkg-config cmake python3-venv

RUN python3 -m venv /helper && . /helper/bin/activate && \
          /helper/bin/pip install --upgrade pip && \
          /helper/bin/pip install docker dbus-python mdns-publisher && \
          /helper/bin/pip freeze > /helper/requirements.txt

COPY dockersock_watcher.py /helper

CMD . /helper/bin/activate && /helper/bin/python3 /helper/dockersock_watcher.py
