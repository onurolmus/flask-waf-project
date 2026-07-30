FROM postgres:14

# Bucardo requires plperl extension and DBI/DBD::Pg in PostgreSQL
RUN apt-get update && \
    apt-get install -y postgresql-plperl-14 libdbd-pg-perl && \
    rm -rf /var/lib/apt/lists/*
