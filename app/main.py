import os
import secrets
from flask import Blueprint, current_app, flash, jsonify, redirect, request, render_template, url_for
from datetime import datetime
from flask_login import current_user, login_required
from sqlalchemy import or_, and_
import qrcode
import json
from app import db
from models.model import Event, EventMode, User, event_attendees, EventVisibility, Eventtag, JoinRequest , Attendee, EventNotification

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
@main_blueprint.route("/user/profile", methods=["GET"])
@login_required
def user_profile():
    """
    Display the user's personal profile with tabs showing:
    - Events they registered for (attending_events)
    - Events they created (created_events)
    """
    # Get current user with all necessary relationships
    user = User.query.options(
        db.joinedload(User.attending_events),
        db.joinedload(User.created_events),
        db.joinedload(User.attendee_links)
    ).get(current_user.id)
    
    return render_template("user_profile.html", user=user)

@main_blueprint.route('/profile', methods=['GET'])
@login_required
def profile():
    """
    Display all events with dynamic filtering support
    Supports multiple filters of the same type: title, organizer, tag, location, mode, date, visibility
    """
    
    # DEBUG: Print received parameters
    # print("=" * 50)
    # print("DEBUG - Received URL parameters:")
    # print(f"request.args: {request.args}")
    # print("=" * 50)
    
    # Collect filter parameters - now supports multiple values per filter type
    filters = {
        "title": request.args.getlist("title"),
        "organizer": request.args.getlist("organizer"),
        "tag": request.args.getlist("tag"),
        "location": request.args.getlist("location"),
        "mode": request.args.getlist("mode"),
        "date": request.args.getlist("date"),
        "visibility": request.args.getlist("visibility"),
    }
    
    # DEBUG: Print parsed filters
    #print("DEBUG - Parsed filters:")
    for key, values in filters.items():
        if values:
            pass
           # print(f"  {key}: {values}")
    #print("=" * 50)

    # Base query
    query = Event.query

    # Apply filters with OR logic for multiple values of same type
    if filters["title"]:
        title_conditions = [Event.title.ilike(f"%{t}%") for t in filters["title"]]
        query = query.filter(or_(*title_conditions))
       # print(f"Applied title filter: {filters['title']}")

    if filters["organizer"]:
        organizer_conditions = [
            Event.creator.has(username=org) for org in filters["organizer"]
        ]
        query = query.filter(or_(*organizer_conditions))
       # print(f"Applied organizer filter: {filters['organizer']}")

    if filters["tag"]:
        tag_conditions = [Event.tags.ilike(f"%{t}%") for t in filters["tag"]]
        query = query.filter(or_(*tag_conditions))
       # print(f"Applied tag filter: {filters['tag']}")

    if filters["location"]:
        location_conditions = [Event.venue.ilike(f"%{loc}%") for loc in filters["location"]]
        query = query.filter(or_(*location_conditions))
       # print(f"Applied location filter: {filters['location']}")

    if filters["mode"]:
        mode_conditions = [Event.mode.ilike(f"%{m}%") for m in filters["mode"]]
        query = query.filter(or_(*mode_conditions))
       # print(f"Applied mode filter: {filters['mode']}")

    if filters["date"]:
        date_conditions = []
        for date_str in filters["date"]:
            try:
                # Try to parse date in various formats
                parsed_date = None
                for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%d %b %Y']:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue
                
                if parsed_date:
                    date_conditions.append(Event.date == parsed_date)
                    print(f"Parsed date: {date_str} -> {parsed_date}")
            except Exception as e:
               # print(f"Failed to parse date: {date_str}, error: {e}")
                pass  # Invalid date format, skip this date
        
        if date_conditions:
            query = query.filter(or_(*date_conditions))
           # print(f"Applied date filter with {len(date_conditions)} conditions")

    if filters["visibility"]:
        visibility_conditions = [Event.visibility == vis for vis in filters["visibility"]]
        query = query.filter(or_(*visibility_conditions))
       # print(f"Applied visibility filter: {filters['visibility']}")

    # Final sorted events
    events = query.order_by(Event.date).all()
   # print(f"DEBUG - Found {len(events)} events after filtering")
   # print("=" * 50)

    # Join request status for each event (if private)
    user_requests = {
        req.event_id: req.status
        for req in JoinRequest.query.filter_by(user_id=current_user.id).all()
    }

    # Fetch events where current user has enabled notifications
    user_notified_event_ids = [
        n.event_id for n in EventNotification.query.filter_by(user_id=current_user.id).all()
    ]

    # Fetch pending private requests if needed
    user_requests = {}  # optional: populate if using private events

    return render_template(
        "profile.html",
        events=events,
        user_requests=user_requests,
        user_notified_event_ids=user_notified_event_ids
    )


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


@events_blueprint.route("/create", methods=["POST"])
@login_required
def create_event():
    data = request.get_json() if request.is_json else request.form

    try:
        # Date & time
        try:
            date_value = datetime.strptime(data.get("date"), "%Y-%m-%d").date() if data.get("date") else None
        except ValueError:
            date_value = None

        try:
            start_value = datetime.strptime(data.get("starttime"), "%H:%M").time() if data.get("starttime") else None
        except ValueError:
            start_value = None

        try:
            end_value = datetime.strptime(data.get("endtime"), "%H:%M").time() if data.get("endtime") else None
        except ValueError:
            end_value = None

        # Mode & visibility
        mode_value = (data.get("mode") or "online").lower()
        visibility_value = (data.get("visibility") or "public").lower()

        # Capacity
        capacity = int(data.get("capacity") or 100)

        event = Event(
            title=data.get("title"),
            description=data.get("description"),
            date=date_value,
            starttime=start_value,
            endtime=end_value,
            mode=EventMode(mode_value),
            visibility=EventVisibility(visibility_value),
            venue=data.get("venue"),
            capacity=capacity,
            organizer_id=current_user.id,
            tags=Eventtag(data.get("tags") or ""),
        )

        db.session.add(event)
        db.session.commit()
        return redirect(url_for("main.profile"))

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


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

    return render_template("event_details.html", event=event)



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


@attendees_blueprint.route('/event/<int:event_id>/scan', methods=["GET"])
@login_required
def scan_qr_page(event_id):
    """
    Render the QR code scanner page for marking attendance
    Only event organizers can access this page
    """
    event = Event.query.get_or_404(event_id)
    
    # Only event organizer can scan QR codes
    if event.organizer_id != current_user.id:
        flash("You are not authorized to scan QR codes for this event!", "danger")
        return redirect(url_for("main.profile"))
    
    return render_template('cam.html', event=event)


# -------------------------------------
# TEST ATTENDANCE ENDPOINT PAGE (For debugging)
# -------------------------------------
@attendees_blueprint.route('/test-attendance', methods=["GET"])
@login_required
def test_attendance_page():
    """
    Test page to manually test the mark_attendance endpoint
    """
    return render_template('test_attendance.html')



# -------------------------------------
# PROCESS QR CODE SCAN (Mark attendance)
# -------------------------------------
@attendees_blueprint.route('/mark-attendance', methods=["POST"])
@login_required
def mark_attendance():
    """
    Process scanned QR code data and mark attendance
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    attendee_id = data.get("attendee_id")
    event_id = data.get("event_id")
    user_id = data.get("user_id")
    token = data.get("token")

    if not all([attendee_id, event_id, user_id, token]):
        return jsonify({"error": "Missing required fields"}), 400

    # Verify event exists and current user is organizer
    event = Event.query.get_or_404(event_id)
    if event.organizer_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    # Find attendee record
    attendee = Attendee.query.filter_by(
        id=attendee_id,
        event_id=event_id,
        user_id=user_id,
        token=token
    ).first()

    if not attendee:
        return jsonify({"error": "Invalid QR code or attendee not found"}), 404

    # Check if already marked present
    if attendee.has_attended:
        return jsonify({
            "success": True,
            "message": f"{attendee.user.username} was already marked as attended",
            "already_marked": True
        }), 200

    # Mark attendance
    attendee.has_attended = True
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Attendance marked for {attendee.user.username}",
        "attendee_name": attendee.user.username,
        "event_name": event.title
    }), 200


# -------------------------------------
# REGISTER FOR EVENT (PUBLIC/PRIVATE LOGIC)
# -------------------------------------
@attendees_blueprint.route("/register", methods=["POST"])
@login_required
def create_attendee():
    event_id = request.form.get("eventId")
    if not event_id:
        return "eventId missing", 400

    event = Event.query.get_or_404(event_id)

    # Organizer cannot register for their own event
    if event.organizer_id == current_user.id:
        flash("You cannot register for your own event!", "danger")
        return redirect(url_for("main.profile"))

    # Check if already registered (check both Attendee table AND many-to-many)
    existing_attendee = Attendee.query.filter_by(
        user_id=current_user.id,
        event_id=event_id
    ).first()
    
    if existing_attendee or current_user in event.attendees:
        flash("You are already registered for this event!", "warning")
        return redirect(url_for("main.profile"))

    # PRIVATE EVENT → Send join request instead of registering
    if event.visibility == EventVisibility.private:
        existing_request = JoinRequest.query.filter_by(
            event_id=event.id,
            user_id=current_user.id
        ).first()

        if not existing_request:
            new_req = JoinRequest(
                event_id=event.id,
                user_id=current_user.id,
                status="pending"
            )
            db.session.add(new_req)
            db.session.commit()

        flash("Join request sent! Please wait for approval.", "info")
        return redirect(url_for("main.profile"))

    # PUBLIC EVENT → Register directly
    # Check capacity
    current_attendees = Attendee.query.filter_by(event_id=event_id).count()
    if current_attendees >= event.capacity:
        flash("Sorry, this event is full!", "danger")
        return redirect(url_for("main.profile"))

    # Generate unique token
    token = secrets.token_urlsafe(32)

    # Create attendee record
    attendee = Attendee(
        user_id=current_user.id,
        event_id=event_id,
        token=token
    )

    db.session.add(attendee)
    db.session.flush()  # Get attendee.id

    # ✅ CRITICAL FIX: Add user to the many-to-many relationship
    if current_user not in event.attendees:
        event.attendees.append(current_user)

    # Create QR Code metadata
    qr_data = {
        "attendee_id": attendee.id,
        "user_id": current_user.id,
        "event_id": event_id,
        "token": token,
        "username": current_user.username,
        "event_name": event.title
    }

    qr_content = json.dumps(qr_data)

    # Generate QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)

    # Save QR image
    img = qr.make_image(fill_color="black", back_color="white")
    qr_dir = os.path.join(current_app.root_path, "static", "qr_codes")
    os.makedirs(qr_dir, exist_ok=True)

    qr_filename = f"qr_{current_user.id}_{event_id}_{attendee.id}.png"
    qr_path = os.path.join(qr_dir, qr_filename)
    img.save(qr_path)

    # Store QR path
    attendee.qr_code_path = f"qr_codes/{qr_filename}"

    db.session.commit()

    flash("Successfully registered for the event!", "success")
    return redirect(url_for("attendees.registration_success", attendee_id=attendee.id))


@attendees_blueprint.route('/registration-success/<int:attendee_id>')
@login_required
def registration_success(attendee_id):
    attendee = Attendee.query.get_or_404(attendee_id)
    
    # Security check: only show to the registered user
    if attendee.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('main.profile'))
    
    event = attendee.event
    
    return render_template('registration_success.html', 
                         attendee=attendee, 
                         event=event)


# -------------------------------------
# UNREGISTER
# -------------------------------------
@attendees_blueprint.route("/unregister/<int:event_id>", methods=["POST"])
@login_required
def unregister_attendee(event_id):
    event = Event.query.get_or_404(event_id)

    # Check if user is registered
    if current_user not in event.attendees:
        flash("You are not registered for this event!", "warning")
        return redirect(url_for("main.profile"))

    # Remove from many-to-many relationship
    event.attendees.remove(current_user)
    
    # ✅ DELETE THE ATTENDEE RECORD (with QR code)
    attendee = Attendee.query.filter_by(
        user_id=current_user.id,
        event_id=event_id
    ).first()
    
    if attendee:
        # Optional: Delete the QR code file from disk
        if attendee.qr_code_path:
            qr_file_path = os.path.join(
                current_app.root_path, 
                "static", 
                attendee.qr_code_path
            )
            if os.path.exists(qr_file_path):
                os.remove(qr_file_path)
        
        db.session.delete(attendee)
    
    db.session.commit()
    
    flash("Successfully unregistered from the event!", "success")
    return redirect(url_for("main.profile"))


# -------------------------------------
# VIEW EVENT ATTENDEES
# -------------------------------------
@attendees_blueprint.route('/event/<int:event_id>/attendees')
@login_required
def get_attendee(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Get all attendees for this event
    attendees = Attendee.query.filter_by(event_id=event_id).all()
    
    return render_template('attendees_list.html', 
                         event=event, 
                         attendees=attendees)

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


# -------------------------------------
# MY EVENTS PAGE (Organizers & Admin)
# -------------------------------------
@events_blueprint.route('/my-events', methods=['GET', 'POST'])

def my_events_page():

    search_query = ""

    # If form submitted
    if request.method == "POST":
        search_query = request.form.get("search", "").strip()

        # Filter events by name or description
        events = Event.query.filter(
            Event.name.ilike(f"%{search_query}%")
        ).all()

        return render_template(
            "profile.html",
            events=events,
            search_query=search_query
        )

    # Default: show all events
    events = Event.query.all()

    return render_template(
        "profile.html",
        events=events,
        search_query=search_query
    )

@events_blueprint.route("/toggle-notification", methods=["POST"])
@login_required
def toggle_notification():
    data = request.get_json()
    event_id = data.get("event_id")
    enabled = data.get("enabled", False)

    if not event_id:
        return jsonify({"error": "Missing event ID"}), 400

    notif = EventNotification.query.filter_by(user_id=current_user.id, event_id=event_id).first()

    if enabled:
        if not notif:
            notif = EventNotification(user_id=current_user.id, event_id=event_id)
            db.session.add(notif)
            db.session.commit()
        return jsonify({"message": f"Notifications enabled for event {event_id}"})
    else:
        if notif:
            db.session.delete(notif)
            db.session.commit()
        return jsonify({"message": f"Notifications disabled for event {event_id}"})