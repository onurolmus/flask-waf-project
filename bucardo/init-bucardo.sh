#!/bin/bash
set -e

echo "Waiting for db1 and db2 to be ready..."
export PGPASSWORD=${DB_PASSWORD}
until pg_isready -h db1 -U ${DB_USER}; do sleep 2; done
until pg_isready -h db2 -U ${DB_USER}; do sleep 2; done

echo "Waiting for Flask migrations to create tables on db1..."
until psql -h db1 -U ${DB_USER} -d ${DB_NAME} -c "SELECT 1 FROM users LIMIT 1;" > /dev/null 2>&1; do
    echo "Tables not found yet. Waiting..."
    sleep 5
done

# Wait for DB2 tables as well to be safe
echo "Waiting for Flask migrations on db2..."
until psql -h db2 -U ${DB_USER} -d ${DB_NAME} -c "SELECT 1 FROM users LIMIT 1;" > /dev/null 2>&1; do
  sleep 2
done

echo "Preparing source databases with necessary extensions for Bucardo..."
for db in db1 db2; do
  psql -h $db -U ${DB_USER} -d ${DB_NAME} -c "CREATE EXTENSION IF NOT EXISTS plpgsql;"
  psql -h $db -U ${DB_USER} -d ${DB_NAME} -c "CREATE EXTENSION IF NOT EXISTS plperl;"
done

echo "Configuring sequences for active-active conflict avoidance..."
# db1 will use odd numbers, db2 will use even numbers
psql -h db1 -U ${DB_USER} -d ${DB_NAME} -c "ALTER SEQUENCE users_id_seq INCREMENT BY 2 RESTART WITH 1;"
psql -h db1 -U ${DB_USER} -d ${DB_NAME} -c "ALTER SEQUENCE online_users_id_seq INCREMENT BY 2 RESTART WITH 1;"

psql -h db2 -U ${DB_USER} -d ${DB_NAME} -c "ALTER SEQUENCE users_id_seq INCREMENT BY 2 RESTART WITH 2;"
psql -h db2 -U ${DB_USER} -d ${DB_NAME} -c "ALTER SEQUENCE online_users_id_seq INCREMENT BY 2 RESTART WITH 2;"

echo "Setting up Bucardo internal database..."
mkdir -p /var/run/bucardo /var/log/bucardo

cat <<EOF > /etc/bucardorc
dbhost = db1
dbport = 5432
dbname = bucardo
dbuser = bucardo
EOF

export PGPASSWORD=${DB_PASSWORD}

# Clean up any partial or broken previous installations
psql -h db1 -U ${DB_USER} -d ${DB_NAME} -c "DROP SCHEMA IF EXISTS bucardo CASCADE;" > /dev/null 2>&1 || true
psql -h db1 -U ${DB_USER} -d postgres -c "DROP DATABASE IF EXISTS bucardo;" > /dev/null 2>&1 || true
psql -h db1 -U ${DB_USER} -d postgres -c "DROP ROLE IF EXISTS bucardo;" > /dev/null 2>&1 || true

# Install Bucardo metadata onto the default bucardo database (connecting via postgres db initially)
bucardo install --dbhost=db1 --dbport=5432 --dbname=postgres --dbuser=${DB_USER} --batch

echo "Configuring Bucardo sync..."
# Add databases
bucardo add database db1 dbname=${DB_NAME} host=db1 user=${DB_USER} pass=${DB_PASSWORD}
bucardo add database db2 dbname=${DB_NAME} host=db2 user=${DB_USER} pass=${DB_PASSWORD}

# Create dbgroup and add databases
bucardo add dbgroup mygroup db1:source db2:source

# Assign tables to the sync so it is not empty, allowing Bucardo to create necessary triggers
bucardo add sync mysync tables=users,online_users dbs=mygroup

echo "Starting Bucardo daemon..."
bucardo start

echo "Tailing Bucardo logs..."
tail -f /var/log/bucardo/log.bucardo
