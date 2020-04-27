#!/bin/bash
set -e # exit if a command exits with a not-zero exit code

POSTGRES="psql -U postgres"

# create a shared role to read & write hive datasets into postgres
echo "Creating database role: hive"
$POSTGRES <<-EOSQL
CREATE USER hive WITH
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION
    PASSWORD '$HIVE_PASSWORD';
EOSQL
