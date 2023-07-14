from flask_socketio import join_room
from context.sockets import socketio
import json

def campaign_initialization_handler():
    @socketio.on('subscribe_campaign_initialization')
    def on_subscribe_campaign_initialization(data):
        print(f"Received subscription request for campaign initialization {data}")

        campaign_id = data['campaign_id']
        join_room(f'subscribe_campaign_initialization_{campaign_id}')
        print(f"Joined room for campaign initialization {campaign_id}")
        socketio.emit('message', f"Joined room for campaign initialization {campaign_id}")

    @socketio.on('subscribe_sender_confirmation')
    def on_subscribe_sender_confirmation(data):
        print(f"Received subscription request for sender confirmation {data}")

        sender_id = data['sender_id']
        join_room(f'subscribe_sender_confirmation_{sender_id}')
        print(f"Joined room for sender confirmation {sender_id}")
        socketio.emit('message', f"Joined room for sender confirmation {sender_id}")
