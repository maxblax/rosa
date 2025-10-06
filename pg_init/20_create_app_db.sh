#!/bin/bash
set -e

POSTGRES="psql --username ${POSTGRES_USER}"

echo "Creating database: ${APP_DB}"

$POSTGRES <<EOSQL
CREATE DATABASE ${APP_DB} OWNER ${APP_USER};
EOSQL
