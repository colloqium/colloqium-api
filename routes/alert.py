'''
The api route for alerts. Get alerts, by campaign ID, Sender ID, or Voter ID. PUT to update the alerts status with the alert ID
'''
from flask import Blueprint, jsonify, request
from models.interaction import Alert
from context.database import db

alert_bp = Blueprint('alert', __name__)

alert_bp.add_url_rule("/alert", methods=['GET', 'PUT'])
def alert():
    data = None
    if request.method != 'GET':
        if not request.is_json:
            return jsonify({'error': 'Request body must be JSON', 'status_code': 400}), 400
        data = request.json
    else:
        data = request.args

    if request.method == 'GET':
        return get_alert(data)
    elif request.method == 'PUT':
        return update_alert(data)



def get_alert(data):

    # check if campaign id, voter id, or sender id are in the data
    # search for alerts based on which is present
    # return the alert list
    if data.get("campaign_id"):
        campaign_id = data["campaign_id"]
        alerts = Alert.query.filter_by(campaign_id=campaign_id).all()
        return jsonify({'alerts': [alert.to_dict() for alert in alerts]}), 200
    if data.get("voter_id"):
        voter_id = data["voter_id"]
        alerts = Alert.query.filter_by(voter_id=voter_id).all()
        return jsonify({'alerts': [alert.to_dict() for alert in alerts]}), 200
    if data.get("sender_id"):
        sender_id = data["sender_id"]
        alerts = Alert.query.filter_by(sender_id=sender_id).all()
        return jsonify({'alerts': [alert.to_dict() for alert in alerts]}), 200
    if data.get("alert_id"):
        alert_id = data["alert_id"]
        alert = Alert.query.filter_by(id=alert_id).first()
        return jsonify({'alert': alert.to_dict()}), 200
    else:
        return jsonify({"message": "No alerts found"}), 404
    
def update_alert(data):
    if not data.get("alert_id"):
        return jsonify({"message": "alert_id is required"}), 400
    alert_id = data["alert_id"]
    alert = Alert.query.filter_by(id=alert_id).first()
    if not alert:
        return jsonify({"message": "Alert not found"}), 404
    if data.get("alert_status"):
        alert.alert_status = data["alert_status"]
    db.session.add(alert)
    db.session.commit()
    return jsonify({"alert": alert.to_dict()}), 200