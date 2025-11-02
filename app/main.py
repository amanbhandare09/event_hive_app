from flask import Blueprint, flash, jsonify, redirect, request, render_template, url_for
from datetime import datetime

from flask_login import current_user, login_required
from app import db
from models.model import Event, EventMode, User

# Main Blueprint
main_blueprint = Blueprint("main", __name__)
events_blueprint = Blueprint("events", __name__)


@main_blueprint.route("/", methods=["GET"])
def index():
    """Render the homepage"""
    pass

@main_blueprint.route("/profile", methods=["GET"])
def profile():
    """Display user profile"""

    events  = Event.query.all()

    return render_template("profile.html", events=events), 200

@main_blueprint.route("/api/health", methods=["GET"])
def api_health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "API is running"}), 200

# Events Blueprint
events_blueprint = Blueprint("events", __name__, url_prefix="/events")

@events_blueprint.route("/", methods=["GET"])
def list_events():
    events = Event.query.all()

    print(events)

    # data = [
    #     {
    #         "title": event.title,
    #         "description": event.description,
    #         "date": event.date.strftime("%Y-%m-%d"),
    #         "time": event.time.strftime("%H:%M") if event.time else None,
    #         "mode": event.mode.value,
    #         "venue": event.venue,
    #         "capacity": event.capacity
    #     }
    #     for event in events
    # ]

    return render_template('profile.html', events=events), 200

@events_blueprint.route("/create", methods=["POST"])
def create_event():
    data = request.get_json()

    event = Event(
        title=data.get("title"),
        description=data.get("description"),
        date=datetime.fromisoformat(data["date"]).date(),
        time=datetime.strptime(data["time"], "%H:%M").time() if data.get("time") else None,
        mode=EventMode(data["mode"].lower()),
        venue=data.get("venue"),
        capacity=int(data.get("capacity", 100)),
        organizer_id=data.get("organizer_id")
    )

    db.session.add(event)
    db.session.commit()

    return jsonify({"message": "Event created successfully", "event_id": event.id}), 201


@events_blueprint.route("/<int:event_id>", methods=["GET"])
def get_event(event_id):
    """Fetch details for a specific event."""
    event = Event.query.get(event_id)

    if not event:
        return jsonify({"error": "Event not found"}), 404

    data = {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "date": event.date.strftime("%Y-%m-%d"),
        "time": event.time.strftime("%H:%M") if event.time else None,
        "mode": event.mode.value,
        "venue": event.venue,
        "capacity": event.capacity
    }

    return jsonify(data), 200

@events_blueprint.route("/<int:event_id>", methods=["PUT"])
def update_event(event_id):
    """Replace full event details."""
    data = request.get_json()
    event = Event.query.get(event_id)

    if not event:
        return jsonify({"error": "Event not found"}), 404

    # Convert string inputs to proper Python types
    event.title = data.get("title")
    event.description = data.get("description")

    # Parse date and time safely
    event.date = datetime.strptime(data.get("date"), "%Y-%m-%d").date()
    event.time = datetime.strptime(data.get("time"), "%H:%M").time()

    # Handle enum value
    mode_value = data.get("mode")
    event.mode = EventMode(mode_value) if mode_value in EventMode._value2member_map_ else EventMode.online

    event.venue = data.get("venue")
    event.capacity = int(data.get("capacity"))

    db.session.commit()

    return jsonify({"message": f"Event {event_id} updated successfully"}), 200

# @events_blueprint.route("/<int:event_id>", methods=["PATCH"])
# def partial_update_event(event_id):
#     """Partially update an event (e.g., capacity or title)."""
#     return jsonify({"message": f"Event {event_id} partially updated"}), 200

@events_blueprint.route("/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    """Delete a specific event."""
    return jsonify({"message": f"Event {event_id} deleted"}), 200

# @events_blueprint.route("/upcoming", methods=["GET"])
# def upcoming_events():
#     """List upcoming events (next 7 days, by default)."""
#     return jsonify({"message": "Upcoming events list"}), 200

# @events_blueprint.route("/<int:event_id>/attendees", methods=["GET"])
# def event_attendees(event_id):
#     """List all attendees registered for a given event."""
#     return jsonify({"message": f"Attendees for event {event_id}"}), 200


# Attendees Blueprint
attendees_blueprint = Blueprint("attendees", __name__)

# @attendees_blueprint.route("/list_attendees", methods=["GET"])
# def list_attendees():
#     """Retrieve a list of all attendees."""
#     return jsonify({"message": "List of all attendees"}), 200

@attendees_blueprint.route("/register", methods=["POST"])
@login_required
def create_attendee():
    
    eventId = request.form.get("eventId")
    print("FORM DATA:", request.form)
    if not eventId:
        return "eventId missing", 400

    event = Event.query.get(eventId)   # ✅ FIXED

    if not event:
        return "event not found", 404

    # Add user to event
    event.attendees.append(current_user)
    event.capacity -= 1
    db.session.commit()

    return f"User {current_user.id} registered for event {event.title}", 201


#Not working for users registered for events
@attendees_blueprint.route("/attendee/<int:attendee_id>", methods=["GET"])
def get_attendee(attendee_id):
    user = User.query.get(attendee_id)
    if not user:
        return jsonify({"error": "Attendee not found"}), 404

    events = [
        {
            "event_id": e.id,
            "title": e.title,
            "date": e.date.strftime("%Y-%m-%d") if e.date else None,
            "time": e.time.strftime("%H:%M") if e.time else None,
            "venue": e.venue,
            "mode": e.mode.value if e.mode else None,
            "organizer": e.organizer.username if e.organizer else None
        }
        for e in user.attending_events
    ]

    return jsonify({
        "attendee_id": user.id,
        "username": user.username,
        "email": user.email,
        "registered_events_count": len(events),
        "registered_events": events
    }), 200


@attendees_blueprint.route("/<int:attendee_id>", methods=["PUT"])
def update_attendee(attendee_id):
    """Update full attendee record."""
    return jsonify({"message": f"Attendee {attendee_id} updated"}), 200

# @attendees_blueprint.route("/<int:attendee_id>/events", methods=["GET"])
# def attendee_events(attendee_id):
#     """List events the attendee is registered for."""
#     return jsonify({"message": f"Events for attendee {attendee_id}"}), 200