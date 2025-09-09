import docker
import os
import re
import sys
import signal
import logging

PUBLISH_TTL = os.environ.get("TTL","120")
# You can switch off the use of avahi for debugging if your local system does not have the avahi daemon running
USE_AVAHI = os.environ.get("USE_AVAHI","yes") == "yes"
# These are the standard python log levels
LOGGING_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
# get local domain from enviroment and escape all period characters
LOCAL_DOMAIN = re.sub(r'\.','\\.',os.environ.get("LOCAL_DOMAIN",".local"))

logger = logging.getLogger("traefik-localhosts")
logging.basicConfig(level=LOGGING_LEVEL)

if USE_AVAHI:
    from mpublisher import AvahiPublisher

class LocalHostWatcher(object):
    """watch the docker socket for starting and dieing containers.
    Publish and unpublish mDNS records to Avahi, using D-BUS."""

    """Set up compiler regexes to find relevant labels / containers"""
    # TODO check for upper/lower case
    hostrule = re.compile(r'traefik\.http\.routers\.(.*)\.rule')
    hostnamerule = re.compile(r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$')

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

        self.localrule = re.compile(r'[Hh][Oo][Ss][Tt]\s*\(\s*`(.*'+LOCAL_DOMAIN+r')`\s*\)')

    def __del__(self):
        logger.info("deregistering all registered hostnames")
        del self.avahi # not strictly necessary but safe

    def publish(self,cname):
        logger.debug("publishing %s",cname)
        if USE_AVAHI:
            self.avahi.publish_cname(cname, True)

    def unpublish(self,cname):
        logger.debug("unpublishing %s",cname)
        if USE_AVAHI:
            self.avahi.unpublish(cname)

    """when start/stop events are received, process the container that triggered the event """
    def process_event(self,event):
        if event['Type'] == 'container' and event['Action'] in ('start','die'):
            container_id = event['Actor']['ID']
            try:
                container = self.dockerclient.containers.get(container_id)
                self.process_container(event['Action'],container)
            except Exception as e:
                logger.warning("%s",e)
                pass

    """when a container triggered start/stop event, and it has a Host label, take appropriate action"""
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
        # Initial scan of running containers and publish hostnames
        logger.info("registering for already running containers...")

        containers = self.dockerclient.containers.list()
        for container in containers:
            self.process_container("start", container)

        # listen for Docker events and process them
        logger.info("waiting for container start/die...")
        for event in self.dockerclient.events(decode=True):
            self.process_event(event)

def exithandler(a,b):
    logger.info("exiting")
#    avahi = None
#    del localWatcher

    # TODO figure out how and whether to unregister handlers
    sys.exit(0)

def main():
    # Set up a signal handler to exit cleanly

    signal.signal(signal.SIGTERM, exithandler)
    signal.signal(signal.SIGINT, exithandler)
    signal.signal(signal.SIGHUP, exithandler)

    dockerclient = docker.from_env()
    localWatcher = LocalHostWatcher(dockerclient)
    localWatcher.run() # this will never return

if __name__ == '__main__':
    main()

    # we should never get here because main() loops indefinitely
    assert False, "executing unreachable code"
