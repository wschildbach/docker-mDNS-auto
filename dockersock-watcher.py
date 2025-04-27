import docker
import re
import sys
import signal
import logging
logger = logging.getLogger(__name__)

PUBLISH_TTL = 120
RENEW_TTL = PUBLISH_TTL-10
USE_AVAHI = True
LOGGING_LEVEL=logging.DEBUG

if USE_AVAHI:
    from mpublisher import AvahiPublisher

"""set up AvahiPublisher and docker connection"""
try:
    dockerclient = docker.from_env()
    if USE_AVAHI:
        avahi = AvahiPublisher(record_ttl=PUBLISH_TTL)
except Exception as e:
    logging.error("%s",e)
    sys.exit(20)

# list of active host entries
activeHostentry = {}

def publish(cname):
    logger.debug("calling publish %s",cname)
    # schedule a timer to re-register the cnames even when the TTL has passed
    signal.alarm(RENEW_TTL)
    if USE_AVAHI:
        avahi.publish_cname(cname, True)

def unpublish(cname):
    logger.debug("calling unpublish %s",cname)
    if len(activeHostentry) == 0:
        # unregister the alarm when the list is empty
        signal.alarm(0)

    if USE_AVAHI:
        avahi.unpublish(cname)

"""Set up compiler regexes to find relevant labels / containers"""
# TODO check for upper/lower case
hostrule = re.compile(r'traefik\.http\.routers\.(.*)\.rule')
localrule = re.compile(r'Host\s*\(\s*`(.*\.local)`\s*\)')
hostnamerule = re.compile(r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$')

"""when start/stop events are received, process the container that triggered the event """
def process_event(event):
    if event['Type'] == 'container' and event['Action'] in ('start','die'):
        container_id = event['Actor']['ID']
        container = dockerclient.containers.get(container_id)

        process_container(event['Action'],container)

"""when a container triggered start/stop event, and it has a Host label, take appropriate action"""
def process_container(action,container):
    hostkeys = filter(lambda l:hostrule.match(l), container.labels.keys())
    for h in hostkeys:
        rhs = container.labels[h]
        cnamematch = localrule.match(rhs)

        if cnamematch:
            cname = cnamematch.group(1)

            if not hostnamerule.match(cname):
                logger.error("invalid hostname %s rejected",cname)
                continue

            if action == 'start':
                logger.debug("enrolling %s",cname)
                activeHostentry[cname] = 1
                publish(cname)
            elif action == 'die':
                logger.debug("de-enrolling %s",cname)
                del activeHostentry[cname]
                unpublish(cname)

def exithandler(a,b):
    logger.info("exiting")
    # delete alarm
    signal.alarm(0)

    while len(activeHostentry) > 0:
        (c,x) = activeHostentry.popitem()
        unpublish(c)

    # unregister handlers? Not sure how
    sys.exit(0)

def reregister(a,b):
#    print ("reregister called")
    for c in activeHostentry.keys():
        publish(c)

def main():
    # Set the signal handler and a 5-second alarm
    signal.signal(signal.SIGTERM, exithandler)
    signal.signal(signal.SIGINT, exithandler)
    signal.signal(signal.SIGHUP, exithandler)
    signal.signal(signal.SIGALRM, reregister)

    # Initial scan of running containers and publish hostnames
    containers = dockerclient.containers.list()

    logger.info("registering for already running containers...")
    for container in containers:
        process_container("start", container)

    # Listen for Docker events and process them
    logger.info("waiting for container start/die...")
    for event in dockerclient.events(decode=True):
        process_event(event)

if __name__ == '__main__':
    logging.basicConfig(level=LOGGING_LEVEL)
    main()

    # we should never get here because main() loops indefinitely
    assert False, "executing unreachable code"
