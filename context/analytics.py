from dataclasses import dataclass
from context.apis import mixpanel_api_secret
import requests
import json
import time
import uuid


class analytics:
    
    def track(user_id, event, properties):
        url = "https://api.mixpanel.com/import?strict=1"
        headers = {
            "Content-Type": "application/json"
        }
        auth = (mixpanel_api_secret, "")

        # Prepare the event data
        event_data = {
            "event": event,
            "properties": {
                "time": int(time.time()),
                "distinct_id": str(user_id),
                "$insert_id": str(uuid.uuid4()),
                **properties
            }
        }

        # Send the request
        try:
            response = requests.post(
                url,
                auth=auth,
                headers=headers,
                data=json.dumps([event_data])
            )
            response.raise_for_status()
            print(f"Event tracked successfully: {event}")
            print(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error tracking event: {e}")
            on_error(e, [event_data])

@dataclass
class EVENT_OPTIONS:
    initialized = 'Interaction Initialized'
    sent =  'Interaction Sent'
    recieved = 'Interaction Recieved'
    interaction_call_back = 'Interaction Call Back'
    voter_analyzed = 'Voter Analyzed'