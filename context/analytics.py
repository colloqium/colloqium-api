from dataclasses import dataclass
import segment.analytics as analytics
from context.apis import segment_write_key

def on_error(error, items):
    print("An error occurred:", error)

analytics.write_key = segment_write_key
analytics.debug = True
analytics.on_error = on_error

@dataclass
class EVENT_OPTIONS:
    initialized = 'Interactin Initialized'
    sent =  'Interaction Sent'
    recieved = 'Interaction Recieved'