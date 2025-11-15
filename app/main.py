from flask import Blueprint, flash, jsonify, redirect, request, render_template, url_for
from datetime import datetime
from flask_login import current_user, login_required
from app import db
from models.model import Event, EventMode, User, event_attendees, EventVisibility, Eventtag, JoinRequest , Attendee

main_blueprint = Blueprint("main", __name__)
events_blueprint = Blueprint("events", __name__)
attendees_blueprint = Blueprint("attendees", __name__)


# -------------------------------------
# MAIN PAGE
# -------------------------------------
@main_blueprint.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# -------------------------------------
# PROFILE PAGE
# -------------------------------------
@main_blueprint.route("/profile", methods=["GET"])
@login_required
def profile():

    events = Event.query.all()

    # Get all join requests created by the current user
    user_join_requests = JoinRequest.query.filter_by(user_id=current_user.id).all()

    # Format: {event_id: "pending"/"approved"/"rejected"}
    user_requests = {req.event_id: req.status for req in user_join_requests}

    return render_template(
        "profile.html",
        events=events,
        user_requests=user_requests
    ), 200


# -------------------------------------
# VIEW ALL EVENTS (OPTIONAL)
# -------------------------------------
@events_blueprint.route("/", methods=["GET"])
def list_events():
    events = Event.query.all()

    user_requests = {}
    if current_user.is_authenticated:
        reqs = JoinRequest.query.filter_by(user_id=current_user.id).all()
        user_requests = {r.event_id: r.status for r in reqs}

    return render_template("profile.html", events=events, user_requests=user_requests)


# -------------------------------------
# CREATE EVENT PAGE
# -------------------------------------
@events_blueprint.route("/create", methods=["GET"])
@login_required
def create_event_page():
    return render_template("create.html")


# -------------------------------------
# CREATE EVENT (POST)
# -------------------------------------
@events_blueprint.route("/create", methods=["POST"])
@login_required
def create_event():

    data = request.get_json() if request.is_json else request.form

    # Safe date parsing
    date_value = data.get("date")
    if isinstance(date_value, str) and date_value:
        date_value = datetime.strptime(date_value, "%Y-%m-%d").date()

    start_value = data.get("starttime")
    if isinstance(start_value, str) and start_value:
        start_value = datetime.strptime(start_value, "%H:%M").time()

    end_value = data.get("endtime")
    if isinstance(end_value, str) and end_value:
        end_value = datetime.strptime(end_value, "%H:%M").time()

    event = Event(
        title=data.get("title"),
        description=data.get("description"),
        date=date_value,
        starttime=start_value,
        endtime=end_value,
        mode=EventMode(data["mode"].lower()),
        visibility=EventVisibility(data["visibility"].lower()),
        venue=data.get("venue"),
        capacity=int(data.get("capacity", 100)),
        organizer_id=current_user.id,
        tags=Eventtag(data["tags"]),
    )

    db.session.add(event)
    db.session.commit()

    return redirect(url_for("main.profile"))


# -------------------------------------
# GET EVENT DETAILS
# -------------------------------------
@events_blueprint.route("/<int:event_id>", methods=["GET"])
def get_event(event_id):
    event = Event.query.get(event_id)
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
        "tags": event.tags.value
    }

    return jsonify(data), 200


# -------------------------------------
# UPDATE EVENT PAGE
# -------------------------------------
@events_blueprint.route("/update_event/<int:event_id>", methods=["GET"])
@login_required
def load_update_event_page(event_id):
    event = Event.query.get(event_id)
    if not event:
        return "Event Not Found", 404
    return render_template("update.html", event=event)


# -------------------------------------
# UPDATE EVENT
# -------------------------------------
@events_blueprint.route("/update_event/<int:event_id>", methods=["POST"])
@login_required
def update_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"message": "Event not found"}), 404

    try:
        data = request.get_json()

        event.title = data.get("title")
        event.description = data.get("description")

        if isinstance(data.get("date"), str):
            event.date = datetime.strptime(data.get("date"), "%Y-%m-%d").date()

        if isinstance(data.get("starttime"), str):
            event.starttime = datetime.strptime(data["starttime"], "%H:%M").time()

        if isinstance(data.get("endtime"), str):
            event.endtime = datetime.strptime(data["endtime"], "%H:%M").time()

        event.mode = EventMode(data["mode"].lower())
        event.venue = data.get("venue")
        event.capacity = int(data.get("capacity"))
        event.tags = Eventtag(data.get("tags"))

        db.session.commit()
        return jsonify({"message": "Event updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 400


# -------------------------------------
# DELETE EVENT
# -------------------------------------
@events_blueprint.route("/<int:event_id>", methods=["DELETE", "POST"])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)

    if event.organizer_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    db.session.delete(event)
    db.session.commit()

    return redirect(url_for("main.profile"))


# -------------------------------------
# REGISTER FOR EVENT (PUBLIC/PRIVATE LOGIC)
# -------------------------------------
@attendees_blueprint.route("/register", methods=["POST"])
@login_required
def create_attendee():

    eventId = request.form.get("eventId")
    if not eventId:
        return "eventId missing", 400

    event = Event.query.get(eventId)
    if not event:
        return "event not found", 404

    # Organizer cannot register their own event
    if event.organizer_id == current_user.id:
        return jsonify({"error": "You cannot register for your own event"}), 400

    # Already attendee
    if current_user in event.attendees:
        return jsonify({"error": "Already registered"}), 400

    # PRIVATE EVENT -> send join request
    if event.visibility == EventVisibility.private:

        existing = JoinRequest.query.filter_by(
            event_id=event.id,
            user_id=current_user.id
        ).first()

        if not existing:
            new_req = JoinRequest(
                event_id=event.id,
                user_id=current_user.id,
                status="pending"
            )
            db.session.add(new_req)
            db.session.commit()

        return redirect(url_for("main.profile"))

    # PUBLIC EVENT -> register directly
    if event.capacity <= 0:
        return jsonify({"error": "Event is full"}), 400

    event.attendees.append(current_user)
    event.capacity -= 1
    db.session.commit()

    return redirect(url_for("main.profile"))


# -------------------------------------
# UNREGISTER
# -------------------------------------
@attendees_blueprint.route("/unregister/<int:event_id>", methods=["POST"])
@login_required
def unregister_attendee(event_id):
    event = Event.query.get_or_404(event_id)

    if current_user not in event.attendees:
        return jsonify({"message": "You are not registered"}), 400

    event.attendees.remove(current_user)
    db.session.commit()

    return redirect(url_for("main.profile"))


# -------------------------------------
# VIEW EVENT ATTENDEES
# -------------------------------------
@attendees_blueprint.route("/event/<int:event_id>/attendees", methods=["GET"])
def get_attendee(event_id):
    event = Event.query.get_or_404(event_id)
    attendees = event.attendees
    return render_template("eventattend.html", event=event, attendees=attendees)

# -------------------------------------
# APPROVE JOIN REQUEST
# -------------------------------------
@events_blueprint.route("/<int:request_id>/approve", methods=["POST"])
@login_required
def approve_request(request_id):
    req = JoinRequest.query.get_or_404(request_id)
    event = req.event

    # Only organizer can approve
    if event.organizer_id != current_user.id:
        return "Unauthorized", 403

    # Approve
    req.status = "approved"

    # Add user to event attendees
    if req.user not in event.attendees:
        event.attendees.append(req.user)
        event.capacity -= 1  # reduce event seats

    db.session.commit()
    return redirect(url_for("events.view_join_requests", event_id=event.id))


# -------------------------------------
# REJECT JOIN REQUEST
# -------------------------------------
@events_blueprint.route("/<int:request_id>/reject", methods=["POST"])
@login_required
def reject_request(request_id):
    req = JoinRequest.query.get_or_404(request_id)
    event = req.event

    # Only organizer can reject
    if event.organizer_id != current_user.id:
        return "Unauthorized", 403

    req.status = "rejected"
    db.session.commit()

    return redirect(url_for("events.view_join_requests", event_id=event.id))


# -------------------------------------
# LIVE EVENTS
# -------------------------------------
@events_blueprint.route("/live")
@login_required
def live_events():
    now = datetime.now()
    today = now.date()
    current_time = now.time()

    live_events = Event.query.filter(
        Event.date == today,
        Event.starttime <= current_time,
        Event.endtime >= current_time
    ).all()

    return render_template("live.html", events=live_events, now=now)

# -------------------------------------
# VIEW JOIN REQUESTS FOR AN EVENT
# -------------------------------------
@events_blueprint.route("/<int:event_id>/requests", methods=["GET"])
@login_required
def view_join_requests(event_id):
    event = Event.query.get_or_404(event_id)

    # Only organizer can view the join requests
    if event.organizer_id != current_user.id:
        return "Unauthorized", 403

    # Fetch all join requests for this event
    requests = JoinRequest.query.filter_by(event_id=event_id).all()

    return render_template("join_requests.html", event=event, requests=requests)

