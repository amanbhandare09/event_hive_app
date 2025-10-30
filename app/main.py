from flask import Blueprint, jsonify, request, render_template

# Main Blueprint
main_blueprint = Blueprint('main', __name__)


@main_blueprint.route('/')
def index():
    return render_template("index.html")

@main_blueprint.route("/profile")
def profile():
    return "Profile"

@main_blueprint.route('/api', methods=['GET'])
def api_health():
    return jsonify({"message": "API is running"}), 200

# Events Blueprint
events_blueprint = Blueprint('events', __name__)

@events_blueprint.route('/', methods=['GET'])
def list_events():
    return jsonify({"message": "List all events"}), 200

@events_blueprint.route('/', methods=['POST'])
def create_event():
    return jsonify({"message": "Create a new event"}), 201

@events_blueprint.route('/<int:event_id>', methods=['GET'])
def get_event(event_id):
    return jsonify({"message": f"Get event {event_id}"}), 200

@events_blueprint.route('/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    return jsonify({"message": f"Update event {event_id}"}), 200

@events_blueprint.route('/<int:event_id>', methods=['PATCH'])
def partial_update_event(event_id):
    return jsonify({"message": f"Partially update event {event_id}"}), 200

@events_blueprint.route('/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    return jsonify({"message": f"Delete event {event_id}"}), 200

@events_blueprint.route('/upcoming', methods=['GET'])
def upcoming_events():
    return jsonify({"message": "List upcoming events"}), 200

@events_blueprint.route('/<int:event_id>/attendees', methods=['GET'])
def event_attendees(event_id):
    return jsonify({"message": f"List attendees for event {event_id}"}), 200

# Attendees Blueprint
attendees_blueprint = Blueprint('attendees', __name__)

@attendees_blueprint.route('/', methods=['GET'])
def list_attendees():
    return jsonify({"message": "List all attendees"}), 200

@attendees_blueprint.route('/', methods=['POST'])
def create_attendee():
    return jsonify({"message": "Register a new attendee"}), 201

@attendees_blueprint.route('/<int:attendee_id>', methods=['GET'])
def get_attendee(attendee_id):
    return jsonify({"message": f"Get attendee {attendee_id}"}), 200

@attendees_blueprint.route('/<int:attendee_id>', methods=['PUT'])
def update_attendee(attendee_id):
    return jsonify({"message": f"Update attendee {attendee_id}"}), 200