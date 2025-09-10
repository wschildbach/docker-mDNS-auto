#!/usr/bin/python3

# Copyright (C) 2025 Wolfgang Schildbach
#
# This program is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program.
# If not, see <https://www.gnu.org/licenses/>.

"""A daemon that listens to the docker socket, waiting for starting and stopping containers,
   and registering/deregistering .local domain names when a label mDNS.publish=host.local
   is present """

import os
import re
import logging
from urllib.error import URLError
import docker # pylint: disable=import-error

PUBLISH_TTL = os.environ.get("TTL","120")
# You can switch off the use of avahi for debugging if your local system
# does not have the avahi daemon running
USE_AVAHI = os.environ.get("USE_AVAHI","yes") == "yes"
# These are the standard python log levels
LOGGING_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
# get local domain from enviroment and escape all period characters
LOCAL_DOMAIN = re.sub(r'\.','\\.',os.environ.get("LOCAL_DOMAIN",".local"))

logger = logging.getLogger("traefik-localhosts")
logging.basicConfig(level=LOGGING_LEVEL)

if USE_AVAHI:
    from mpublisher import AvahiPublisher # pylint: disable=import-error

class LocalHostWatcher():
    """watch the docker socket for starting and dieing containers.
    Publish and unpublish mDNS records to Avahi, using D-BUS."""

    # Set up compiler regexes to find relevant labels / containers
    hostrule = re.compile(r'mDNS\.publish')
    hostnamerule = re.compile(r'^\s*[\w\-\.]+\s*$')
    localrule = re.compile(r'.+'+LOCAL_DOMAIN)

    def __init__(self,dockerclient,ttl=PUBLISH_TTL):
        """set up AvahiPublisher and docker connection"""
        logger.debug("LocalHostWatcher.__init__()")

        try:
            self.dockerclient = dockerclient
            if USE_AVAHI:
                self.avahi = AvahiPublisher(record_ttl=PUBLISH_TTL)
        except Exception as e:
            logger.critical("%s",e)
            raise(e)


    def __del__(self):
        # this debug message is a bit of a misnomer. We cannot deregister
        # hostnames, strictly speaking -- they will go out of existence after
        # the TTL by themselves, once we kill the avahi publisher
        logger.info("deregistering all registered hostnames")
        del self.avahi # not strictly necessary but safe

    def publish(self,cname):
        """ publish the given cname using avahi """
        logger.debug("publishing %s",cname)
        if USE_AVAHI:
            self.avahi.publish_cname(cname, True)

    def unpublish(self,cname):
        """ unpublish the given cname using avahi """
        logger.debug("unpublishing %s",cname)
        if USE_AVAHI:
            self.avahi.unpublish(cname)

    def process_event(self,event):
        """when start/stop events are received, process the container that triggered the event """
        if event['Type'] == 'container' and event['Action'] in ('start','die'):
            container_id = event['Actor']['ID']
            try:
                container = self.dockerclient.containers.get(container_id)
                self.process_container(event['Action'],container)
            except URLError as error:
                # in some cases, containers may have already gone away when we process the event.
                # consider this harmless but log an error
                logger.warning("%s",error)

    def process_container(self,action,container):
        hostkeys = filter(lambda l:self.hostrule.match(l), container.labels.keys())
        for h in hostkeys:
            cnamematch = self.localrule.match(container.labels[h])

            if cnamematch:
                cname = cnamematch.group(1)

                if not self.hostnamerule.match(cname):
                    logger.error("invalid hostname %s rejected",cname)
                    continue

                if action == 'start':
                    try:
                        self.publish(cname)
                    except KeyError:
                        logger.warning("registering previously registered %s",cname)
                elif action == 'die':
                    try:
                        self.unpublish(cname)
                    except KeyError:
                        logger.warning("unregistering previously unregistered %s",cname)

    def run(self):
        """Initial scan of running containers and publish hostnames.
             Enumerate all running containers and register them"""

        logger.info("registering for already running containers...")

        containers = self.dockerclient.containers.list()
        for container in containers:
            self.process_container("start", container)

        # listen for Docker events and process them
        logger.info("waiting for container start/die...")
        for event in self.dockerclient.events(decode=True):
            self.process_event(event)

def main():
    dockerclient = docker.from_env()
    localWatcher = LocalHostWatcher(dockerclient)
    localWatcher.run() # this will never return

if __name__ == '__main__':
    main()

    # we should never get here because main() loops indefinitely
    assert False, "executing unreachable code"
