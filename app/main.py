import os
import secrets
from flask import Blueprint, current_app, flash, jsonify, redirect, request, render_template, url_for
from datetime import datetime
from flask_login import current_user, login_required
from sqlalchemy import or_, and_
import qrcode
import json
from app import db
from models.model import Event, EventMode, User, event_attendees, EventVisibility, Eventtag, JoinRequest, Attendee, EventNotification
from app.validators import (
    EventCreateUpdateSchema, 
    EventFilterSchema, 
    AttendeeRegistrationSchema, 
    MarkAttendanceSchema
)
from app.utils import validate_json, validate_form, validate_query

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
    - Archived events count
    """
    # Get current user with all necessary relationships
    user = User.query.options(
        db.joinedload(User.attending_events),
        db.joinedload(User.created_events),
        db.joinedload(User.attendee_links)
    ).get(current_user.id)
    
    # Get archived events count
    archived_count = Event.query.filter_by(
        organizer_id=current_user.id,
        is_archived=True
    ).count()
    
    # ✅ FIX: Filter out archived events from attending_events
    active_attending_events = [
        event for event in user.attending_events 
        if not event.is_archived
    ]
    
    # ✅ FIX: Filter out archived events from created_events
    active_created_events = [
        event for event in user.created_events 
        if not event.is_archived
    ]
    
    # # ✅ NEW: Get saved events
    # saved_events_query = Event.query.join(SavedEvent).filter(
    #     SavedEvent.user_id == current_user.id,
    #     Event.is_archived == False
    # ).all()
    
    return render_template(
        "user_profile.html", 
        user=user, 
        archived_count=archived_count,
        active_attending_events=active_attending_events,
        active_created_events=active_created_events,
        # saved_events=saved_events_query
    )


@main_blueprint.route('/profile', methods=['GET'])
@login_required
def profile():
    """
    Display all events with dynamic filtering support
    Supports multiple filters of the same type: title, organizer, tag, location, mode, date, visibility
    """    
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

    # Base query
    # query = Event.query
    query = Event.query.filter_by(is_archived=False)

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

    
    # 2. CALCULATE THE ARCHIVED COUNT
    # Query all events where is_archived is True for the current user (organizer)
    archived_count = db.session.scalar(
        db.select(db.func.count()).where(
            Event.organizer_id == current_user.id,
            Event.is_archived == True
        )
    )
    
    return render_template(
        "profile.html",
        events=events,
        user_requests=user_requests,
        user_notified_event_ids=user_notified_event_ids,
        archived_count=archived_count 
    )


# -------------------------------------
# VIEW ALL EVENTS (OPTIONAL)
# -------------------------------------
@events_blueprint.route("/", methods=["GET"])
def list_events():
    events = Event.query.filter_by(is_archived=False).all()

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
    try:
        # Validate request data (support both JSON and form)
        if request.is_json:
            data = validate_json(EventCreateUpdateSchema)
        else:
            data = validate_form(EventCreateUpdateSchema)

        # Create event with validated data
        event = Event(
            title=data.title,
            description=data.description,
            date=data.date,
            starttime=data.starttime,
            endtime=data.endtime,
            mode=EventMode(data.mode.value),
            visibility=EventVisibility(data.visibility.value),
            venue=data.venue,
            capacity=data.capacity,
            organizer_id=current_user.id,
            tags=Eventtag(data.tags.value),
        )

        db.session.add(event)
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                "message": "Event created successfully",
                "event_id": event.id
            }), 201
            
        return redirect(url_for("main.profile"))

    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({"error": str(e)}), 500
        flash(f"Error creating event: {str(e)}", "danger")
        return redirect(url_for("events.create_event_page"))


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

    # Check authorization
    if event.organizer_id != current_user.id:
        return jsonify({"message": "Unauthorized"}), 403

    try:
        # Validate request data
        data = validate_json(EventCreateUpdateSchema)

        # Update event with validated data
        event.title = data.title
        event.description = data.description
        event.date = data.date
        event.starttime = data.starttime
        event.endtime = data.endtime
        event.mode = EventMode(data.mode.value)
        event.venue = data.venue
        event.capacity = data.capacity
        event.tags = Eventtag(data.tags.value)

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
    # Validate request data
    data = validate_json(MarkAttendanceSchema)

    # Verify event exists and current user is organizer
    event = Event.query.get_or_404(data.event_id)
    if event.organizer_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    # Find attendee record
    attendee = Attendee.query.filter_by(
        id=data.attendee_id,
        event_id=data.event_id,
        user_id=data.user_id,
        token=data.token
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
# -------------------------------------
# REGISTER FOR EVENT (PUBLIC/PRIVATE LOGIC)
# -------------------------------------
@attendees_blueprint.route("/register", methods=["POST"])
@login_required
def create_attendee():
    try:
        # Validate registration data (support both JSON and form)
        if request.is_json:
            data = validate_json(AttendeeRegistrationSchema)
        else:
            data = validate_form(AttendeeRegistrationSchema)
        event_id = data.eventId
    except Exception as e:
        print(f"Validation Error: {str(e)}")
        if request.is_json:
            return jsonify({"error": f"Validation error: {str(e)}"}), 422
        flash(f"Validation error: {str(e)}", "danger")
        return redirect(url_for("main.profile"))

    event = Event.query.get_or_404(event_id)

    # Organizer cannot register for their own event
    if event.organizer_id == current_user.id:
        if request.is_json:
            return jsonify({"error": "You cannot register for your own event!"}), 403
        flash("You cannot register for your own event!", "danger")
        return redirect(url_for("main.profile"))

    # Check if already registered (check both Attendee table AND many-to-many)
    existing_attendee = Attendee.query.filter_by(
        user_id=current_user.id,
        event_id=event_id
    ).first()
    
    if existing_attendee or current_user in event.attendees:
        if request.is_json:
            return jsonify({"error": "You are already registered for this event!"}), 400
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

        if request.is_json:
            return jsonify({"message": "Join request sent! Please wait for approval."}), 200
        flash("Join request sent! Please wait for approval.", "info")
        return redirect(url_for("main.profile"))

    # PUBLIC EVENT → Register directly
    # Check capacity
    current_attendees = Attendee.query.filter_by(event_id=event_id).count()
    if current_attendees >= event.capacity:
        if request.is_json:
            return jsonify({"error": "Sorry, this event is full!"}), 400
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

    if request.is_json:
        return jsonify({
            "message": "Successfully registered for the event!",
            "attendee_id": attendee.id,
            "qr_code_path": attendee.qr_code_path
        }), 201

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
        Event.endtime >= current_time,
        Event.is_archived == False
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


# -------------------------------------
# VIEW ARCHIVED EVENTS
# -------------------------------------
@events_blueprint.route("/archives", methods=["GET"])
@login_required
def view_archives():
    """View all archived events created by current user"""
    archived_events = Event.query.filter_by(
        organizer_id=current_user.id,
        is_archived=True
    ).order_by(Event.date.desc()).all()

    return render_template("archives.html", events=archived_events)


# -------------------------------------
# RECREATE EVENT FROM ARCHIVE
# -------------------------------------
@events_blueprint.route("/recreate/<int:event_id>", methods=["GET"])
@login_required
def recreate_from_archive(event_id):
    """Load archived event data into a NEW recreation form"""
    event = Event.query.get_or_404(event_id)

    # Only organizer can recreate their own events
    if event.organizer_id != current_user.id:
        flash("You are not authorized to recreate this event!", "danger")
        return redirect(url_for("events.view_archives"))

    # Must be archived
    if not event.is_archived:
        flash("This event is not archived!", "warning")
        return redirect(url_for("main.profile"))

    # Render NEW recreate form with event data
    # Pass 'now' variable for date validation
    return render_template("recreate.html", event=event, now=datetime.now())

@events_blueprint.route("/recreate/<int:event_id>", methods=["POST"])
@login_required
def process_recreation(event_id):
    """Process recreation of archived event"""
    archived_event = Event.query.get_or_404(event_id)

    # Security check
    if archived_event.organizer_id != current_user.id:
        flash("Unauthorized!", "danger")
        return redirect(url_for("events.view_archives"))

    try:
        # Validate request data (support both JSON and form)
        if request.is_json:
            data = validate_json(EventCreateUpdateSchema)
        else:
            data = validate_form(EventCreateUpdateSchema)

        # Create NEW event from archived data
        new_event = Event(
            title=data.title,
            description=data.description,
            date=data.date,
            starttime=data.starttime,
            endtime=data.endtime,
            mode=EventMode(data.mode.value),
            visibility=EventVisibility(data.visibility.value),
            venue=data.venue,
            capacity=data.capacity,
            organizer_id=current_user.id,
            tags=Eventtag(data.tags.value),
            is_archived=False  # New event is NOT archived
        )

        db.session.add(new_event)
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                "message": "Event recreated successfully",
                "event_id": new_event.id
            }), 201
            
        flash("Event recreated successfully!", "success")
        return redirect(url_for("main.profile"))

    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({"error": str(e)}), 500
        flash(f"Error recreating event: {str(e)}", "danger")
        return redirect(url_for("events.view_archives"))
