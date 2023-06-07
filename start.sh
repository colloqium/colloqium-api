#!/bin/bash
# Start Flask app
poetry run python main.py &
# Wait for Flask to start
sleep 5
# Start ngrok
ngrok http --domain=converse.ngrok.app 5000
