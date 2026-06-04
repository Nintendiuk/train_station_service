#!/bin/sh
# wait-for-db.sh

set -e

host="$1"
shift

until pg_isready -h "$host" -p 5432; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "Postgres is up - executing command"
exec "$0"
