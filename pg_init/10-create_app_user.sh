#!/bin/bash
set -e

POSTGRES="psql --username ${POSTGRES_USER}"

echo "Creating database role: ${APP_USER}"

$POSTGRES <<-EOSQL
CREATE USER ${APP_USER} WITH CREATEDB PASSWORD '${APP_USER_PWD}';
EOSQL
