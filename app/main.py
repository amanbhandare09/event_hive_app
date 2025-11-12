from flask import Blueprint, flash, jsonify, redirect, request, render_template, url_for
from datetime import datetime

from flask_login import current_user, login_required
from app import db
from models.model import Event, EventMode, User,event_attendees,EventVisibility, Eventtag

# Main Blueprint
main_blueprint = Blueprint("main", __name__)
events_blueprint = Blueprint("events", __name__)


@main_blueprint.route("/", methods=["GET"])
def index():
    """Render the homepage"""
    return render_template("index.html")
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
events_blueprint = Blueprint("events", __name__)

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

# 🟢 Show Create Event Page
@events_blueprint.route("/create", methods=["GET"])
def create_event_page():
    return render_template("create.html")

# 🟢 Handle Create Event POST (from fetch() or form)
@events_blueprint.route("/create", methods=["POST"])
def create_event():
    # If request has JSON (from fetch)
    if request.is_json:
        data = request.get_json()
    else:
        # Fallback for normal HTML form submission
        data = request.form

    event = Event(
        title=data.get("title"),
        description=data.get("description"),
        date=datetime.fromisoformat(data["date"]).date(),
        starttime=datetime.strptime(data["starttime"], "%H:%M").time() if data.get("starttime") else None,
        mode=EventMode(data["mode"].lower()),
        endtime=datetime.strptime(data["endtime"], "%H:%M").time() if data.get("endtime") else None,
        visibility=EventVisibility(data["visibility"].lower()),
        venue=data.get("venue"),
        capacity=int(data.get("capacity", 100)),
        organizer_id=current_user.id,
        tags=Eventtag(data["tags"])
    )

    db.session.add(event)
    db.session.commit()

    # If JSON (API) → return JSON
    if request.is_json:
        return jsonify({"message": "Event created successfully", "event_id": event.id}), 201
    # Else redirect back to events list page
    else:
        return render_template("create.html", success=True)


@events_blueprint.route("/<int:event_id>", methods=["GET"])
def get_event(event_id):
    """Fetch details for a specific event."""
    event = Event.query.get(event_id)
    attendees = event.attendee
    if not event:
        return jsonify({"error": "Event not found"}), 404

    data = {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "date": event.date.strftime("%Y-%m-%d"),
        "starttime": event.starttime.strftime("%H:%M") if event.starttime else None,
        "endtime": event.endtime.strftime("%H:%M") if event.endtime else None,
        "mode": event.mode.value,
        "venue": event.venue,
        "capacity": event.capacity,
        "tags": event.tags
    }

    return jsonify(data), 200
@events_blueprint.route("/update_event/<int:event_id>", methods=["GET"])
def load_update_event_page(event_id):
    event = Event.query.get(event_id)
    if not event:
        return "Event Not Found", 404
    
    return render_template("update.html", event=event)


@events_blueprint.route("/update_event/<int:event_id>", methods=["POST"])
def update_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"message": "Event not found"}), 404
    
    try:
        data = request.get_json()
        
        # Update event fields
        event.title = data.get("title")
        event.description = data.get("description")
        event.date = datetime.strptime(data.get("date"), "%Y-%m-%d").date()
        event.starttime = datetime.strptime(data.get("starttime"), "%H:%M").time() if data.get("starttime") else None
        event.endtime = datetime.strptime(data.get("endtime"), "%H:%M").time() if data.get("endtime") else None
        event.mode = EventMode(data.get("mode"))
        event.venue = data.get("venue")
        event.capacity = int(data.get("capacity"))
        event.tags = Eventtag(data.get("tags"))
        
        db.session.commit()
        
        return jsonify({"message": "Event updated successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 400


# @events_blueprint.route("/<int:event_id>", methods=["PATCH"])
# def partial_update_event(event_id):
#     """Partially update an event (e.g., capacity or title)."""
#     return jsonify({"message": f"Event {event_id} partially updated"}), 200

@events_blueprint.route("/<int:event_id>", methods=["DELETE", "POST"])
@login_required
def delete_event(event_id):
    """Delete a specific event if the current user is the creator."""
    event = Event.query.get_or_404(event_id)

    # Ensure only the event creator can delete
    if event.organizer_id != current_user.id:
        return jsonify({"error": "Unauthorized: You can only delete your own events."}), 403

    # Delete the event
    db.session.delete(event)
    db.session.commit()

    # Return response (supports API + HTML redirect)
    if "application/json" in str(request.headers.get("Accept")):
        return jsonify({"message": f"Event {event_id} deleted successfully"}), 200
    else:
        return redirect(url_for("main.profile"))

# @events_blueprint.route("/event_update/<int:event_id>", methods=["GET"])
# @login_required
# def load_update_event_page(event_id):
#     event = Event.query.get_or_404(event_id)

#     if event.organizer_id != current_user.id:
#         return "Unauthorized", 403

#     return render_template("update.html", event=event)


# @events_blueprint.route("/event_update/<int:event_id>", methods=["PUT"])
# @login_required
# def update_event(event_id):
#     event = Event.query.get_or_404(event_id)

#     if event.organizer_id != current_user.id:
#         return "Unauthorized", 403

#     event.title = request.form.get("title")
#     event.description = request.form.get("description")
#     event.date = request.form.get("date")
#     event.time = request.form.get("time")
#     event.mode = request.form.get("mode")
#     event.venue = request.form.get("venue")
#     event.capacity = request.form.get("capacity")

#     db.session.commit()

#     return redirect(url_for("events.load_update_event_page", event_id=event_id))




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

    event = Event.query.get(eventId)
    if not event:
        return "event not found", 404

    # Prevent duplicate registration
    if current_user in event.attendees:
        return jsonify({"error": "Already registered for this event"}), 400

    # Prevent organizer from registering for their own event
    if event.organizer_id == current_user.id:
        return jsonify({"error": "You cannot register for your own event"}), 400

    # Check if event still has capacity
    if event.capacity <= 0:
        return jsonify({"error": "Event is full"}), 400

    # Add user to event
    event.attendees.append(current_user)
    event.capacity -= 1

    db.session.commit()
    return redirect(url_for("main.profile"))



#Not working for users registered for events
@attendees_blueprint.route("/event/<int:event_id>/attendees", methods=["GET"])
def get_attendee(event_id):
    """Display all attendees for a specific event."""
    event = Event.query.get_or_404(event_id)

    # Only organizer or admin can see attendees
    # if event.organizer_id != current_user.id:
    #     flash("You are not authorized to view attendees for this event.", "danger")
    #     return redirect(url_for("events.all_events"))

    attendees = event.attendees
    return render_template("eventattend.html", event=event, attendees=attendees)



@attendees_blueprint.route("/unregister/<int:event_id>", methods=["POST"])
@login_required
def unregister_attendee(event_id):
    """Unregister the current user from a given event."""
    event = Event.query.get_or_404(event_id)

    if current_user not in event.attendees:
        return jsonify({"message": "You are not registered for this event"}), 400

    event.attendees.remove(current_user)
    db.session.commit()

    return redirect(url_for("main.profile"))
# @attendees_blueprint.route("/<int:attendee_id>", methods=["PUT"])
# def update_attendee(attendee_id):
#     """Update full attendee record."""
#     return jsonify({"message": f"Attendee {attendee_id} updated"}), 200

# @attendees_blueprint.route("/<int:attendee_id>/events", methods=["GET"])
# def attendee_events(attendee_id):
#     """List events the attendee is registered for."""
#     return jsonify({"message": f"Events for attendee {attendee_id}"}), 200