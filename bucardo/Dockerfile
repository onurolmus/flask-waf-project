FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y bucardo postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Create bucardo log directory and config file
RUN mkdir -p /var/run/bucardo /var/log/bucardo && \
    touch /etc/bucardorc && \
    chown -R postgres:postgres /var/run/bucardo /var/log/bucardo /etc/bucardorc

COPY init-bucardo.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/init-bucardo.sh

USER postgres
WORKDIR /var/lib/postgresql

CMD ["/usr/local/bin/init-bucardo.sh"]
