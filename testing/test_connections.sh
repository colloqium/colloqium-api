#!/bin/bash
# check_connections.sh

# Loop indefinitely until the user stops the script with Ctrl+C
while true; do
  # Use the Heroku CLI to connect and execute the SQL command
  heroku pg:psql PUCE --command "SELECT COUNT(*) FROM pg_stat_activity;"
  
  # Wait for 10 seconds
  sleep 2
done