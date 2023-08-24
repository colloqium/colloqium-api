from flask_socketio import join_room
from context.sockets import socketio
import json

def interaction_evaluation_handler():
    @socketio.on('subscribe_interaction_evaluation')
    def on_subscribe_interaction_evaluation(data):
        print(f"Received subscription request for interaction evaluation {data}")

        interaction_id = data['interaction_id']
        join_room(f'subscribe_interaction_evaluation_{interaction_id}')
        print(f"Joined room for interaction evaluation {interaction_id}")
        socketio.emit('message', f"Joined room for interaction evaluation {interaction_id}")

def funnel_refresh_handler():
    @socketio.on('subscribe_funnel_refresh')
    def on_subscribe_funnel_refresh(data):
        print(f"Received subscription request for funnel refresh {data}")

        campaign_id = data['campaign_id']
        join_room(f'subscribe_funnel_refresh_{campaign_id}')
        print(f"Joined room for funnel refresh {campaign_id}")
        socketio.emit('message', f"Joined room for funnel refresh {campaign_id}")

def campaign_insight_refresh_handler():
    @socketio.on('subscribe_campaign_insight_refresh')
    def on_subscribe_campaign_insight_refresh(data):
        print(f"Received subscription request for campaign insight refresh {data}")

        campaign_id = data['campaign_id']
        join_room(f'subscribe_campaign_insight_refresh_{campaign_id}')
        print(f"Joined room for campaign insight refresh {campaign_id}")
        socketio.emit('message', f"Joined room for campaign insight refresh {campaign_id}")