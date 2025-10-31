from flask import Blueprint, jsonify, request, render_template

# Main Blueprint
main_blueprint = Blueprint("main", __name__)

@main_blueprint.route("/", methods=["GET"])
def index():
    """Render the homepage"""
    return render_template("index.html")

@main_blueprint.route("/profile", methods=["GET"])
def profile():
    """Display user profile"""
    return render_template("profile.html"), 200

@main_blueprint.route("/api/health", methods=["GET"])
def api_health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "API is running"}), 200

# Events Blueprint
events_blueprint = Blueprint("events", __name__, url_prefix="/events")

@events_blueprint.route("/", methods=["GET"])
def list_events():
    """
    Retrieve all events.
    Optional query params: ?upcoming=true or ?limit=10
    """
    return jsonify({"message": "List of all events"}), 200

@events_blueprint.route("/", methods=["POST"])
def create_event():
    """
    Create a new event.
    Expected JSON:
    {
        "name": "Tech Conference",
        "date": "2025-11-10T10:00:00",
        "capacity": 100
    }
    """
    return jsonify({"message": "Event created successfully"}), 201

@events_blueprint.route("/<int:event_id>", methods=["GET"])
def get_event(event_id):
    """Fetch details for a specific event."""
    return jsonify({"message": f"Details for event {event_id}"}), 200

@events_blueprint.route("/<int:event_id>", methods=["PUT"])
def update_event(event_id):
    """Replace full event details."""
    return jsonify({"message": f"Event {event_id} updated"}), 200

@events_blueprint.route("/<int:event_id>", methods=["PATCH"])
def partial_update_event(event_id):
    """Partially update an event (e.g., capacity or title)."""
    return jsonify({"message": f"Event {event_id} partially updated"}), 200

@events_blueprint.route("/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    """Delete a specific event."""
    return jsonify({"message": f"Event {event_id} deleted"}), 200

@events_blueprint.route("/upcoming", methods=["GET"])
def upcoming_events():
    """List upcoming events (next 7 days, by default)."""
    return jsonify({"message": "Upcoming events list"}), 200

@events_blueprint.route("/<int:event_id>/attendees", methods=["GET"])
def event_attendees(event_id):
    """List all attendees registered for a given event."""
    return jsonify({"message": f"Attendees for event {event_id}"}), 200


# Attendees Blueprint
attendees_blueprint = Blueprint("attendees", __name__, url_prefix="/attendees")

@attendees_blueprint.route("/", methods=["GET"])
def list_attendees():
    """Retrieve a list of all attendees."""
    return jsonify({"message": "List of all attendees"}), 200

@attendees_blueprint.route("/", methods=["POST"])
def create_attendee():
    """
    Register a new attendee.
    Expected JSON:
    {
        "name": "John Doe",
        "email": "john@example.com"
    }
    """
    return jsonify({"message": "Attendee registered successfully"}), 201

@attendees_blueprint.route("/<int:attendee_id>", methods=["GET"])
def get_attendee(attendee_id):
    """Fetch details for a specific attendee."""
    return jsonify({"message": f"Details for attendee {attendee_id}"}), 200

@attendees_blueprint.route("/<int:attendee_id>", methods=["PUT"])
def update_attendee(attendee_id):
    """Update full attendee record."""
    return jsonify({"message": f"Attendee {attendee_id} updated"}), 200

@attendees_blueprint.route("/<int:attendee_id>/events", methods=["GET"])
def attendee_events(attendee_id):
    """List events the attendee is registered for."""
    return jsonify({"message": f"Events for attendee {attendee_id}"}), 200
