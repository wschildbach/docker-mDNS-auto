FROM debian:bookworm-slim

#RUN apt update && apt --yes upgrade

ENV DUR=60

RUN echo "echo sleeping && sleep \$DUR && echo waking" >/foo.sh
RUN chmod +x /foo.sh

CMD /bin/bash /foo.sh
