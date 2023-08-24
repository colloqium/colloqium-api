from routes.campaign_initialization import campaign_initialization_handler
from routes.insight_sockets import interaction_evaluation_handler, funnel_refresh_handler, campaign_insight_refresh_handler



def initialize_socket_handlers():
    campaign_initialization_handler()
    interaction_evaluation_handler()
    funnel_refresh_handler()
    campaign_insight_refresh_handler()