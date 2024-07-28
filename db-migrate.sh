#!/bin/bash

# Wait for the database to be ready
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "db" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing migrations"

# Set the Flask app environment variable
export FLASK_APP=main.py

# Run migrations
flask db upgrade

# If migrations were successful, run the application
if [ $? -eq 0 ]; then
  >&2 echo "Migrations completed successfully"
  exec "$@"
else
  >&2 echo "Migration failed"
  exit 1
fi