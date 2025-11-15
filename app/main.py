from flask import Blueprint, current_app, flash, jsonify, redirect, request, render_template, url_for
from datetime import datetime
import secrets
import qrcode
import os

from flask_login import current_user, login_required
from app import db
from models.model import Event, EventMode, User, EventVisibility, Attendee

# Main Blueprint
main_blueprint = Blueprint("main", __name__)
events_blueprint = Blueprint("events", __name__)


@main_blueprint.route("/", methods=["GET"])
def index():
    """Render the homepage"""
    return render_template("index.html")


@main_blueprint.route("/profile", methods=["GET"])
@login_required
def profile():
    """Display user profile"""
    events = Event.query.all()
    return render_template("profile.html", events=events), 200


@main_blueprint.route("/api/health", methods=["GET"])
def api_health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "API is running"}), 200


# Events Blueprint
@events_blueprint.route("/", methods=["GET"])
def list_events():
    events = Event.query.all()
    print(events)
    return render_template('profile.html', events=events), 200


# 🟢 Show Create Event Page
@events_blueprint.route("/create", methods=["GET"])
@login_required
def create_event_page():
    return render_template("create.html")


# 🟢 Handle Create Event POST (from fetch() or form)
@events_blueprint.route("/create", methods=["POST"])
@login_required
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
        time=datetime.strptime(data["time"], "%H:%M").time() if data.get("time") else None,
        mode=EventMode(data["mode"].lower()),
        visibility=EventVisibility(data.get("visibility", "public").lower()),
        venue=data.get("venue"),
        capacity=int(data.get("capacity", 100)),
        organizer_id=current_user.id
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
    
    if not event:
        return jsonify({"error": "Event not found"}), 404

    # Count actual attendees from attendee_links
    attendee_count = len(event.attendee_links)

    data = {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "date": event.date.strftime("%Y-%m-%d"),
        "time": event.time.strftime("%H:%M") if event.time else None,
        "mode": event.mode.value,
        "visibility": event.visibility.value,
        "venue": event.venue,
        "capacity": event.capacity,
        "attendee_count": attendee_count,
        "organizer_id": event.organizer_id
    }

    return jsonify(data), 200


@events_blueprint.route("/update_event/<int:event_id>", methods=["GET"])
@login_required
def load_update_event_page(event_id):
    event = Event.query.get(event_id)
    if not event:
        return "Event Not Found", 404
    
    # Ensure only organizer can update
    if event.organizer_id != current_user.id:
        return "Unauthorized", 403
    
    return render_template("update.html", event=event)


@events_blueprint.route("/update_event/<int:event_id>", methods=["POST"])
@login_required
def update_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"message": "Event not found"}), 404
    
    # Ensure only organizer can update
    if event.organizer_id != current_user.id:
        return jsonify({"message": "Unauthorized"}), 403
    
    try:
        data = request.get_json()
        
        # Update event fields
        event.title = data.get("title")
        event.description = data.get("description")
        event.date = datetime.strptime(data.get("date"), "%Y-%m-%d").date()
        event.time = datetime.strptime(data.get("time"), "%H:%M").time() if data.get("time") else None
        event.mode = EventMode(data.get("mode"))
        event.visibility = EventVisibility(data.get("visibility", event.visibility.value))
        event.venue = data.get("venue")
        event.capacity = int(data.get("capacity"))
        
        db.session.commit()
        
        return jsonify({"message": "Event updated successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 400


@events_blueprint.route("/<int:event_id>", methods=["DELETE", "POST"])
@login_required
def delete_event(event_id):
    """Delete a specific event if the current user is the creator."""
    event = Event.query.get_or_404(event_id)

    # ✅ Ensure only the event creator can delete
    if event.organizer_id != current_user.id:
        return jsonify({"error": "Unauthorized: You can only delete your own events."}), 403

    # ✅ Delete the event (cascade will handle attendee_links)
    db.session.delete(event)
    db.session.commit()

    # ✅ Return response (supports API + HTML redirect)
    if "application/json" in str(request.headers.get("Accept")):
        return jsonify({"message": f"Event {event_id} deleted successfully"}), 200
    else:
        return redirect(url_for("main.profile"))


# Attendees Blueprint
attendees_blueprint = Blueprint("attendees", __name__)


# from flask import render_template, redirect, url_for, request, flash
# import secrets


@attendees_blueprint.route('/register', methods=['POST'])
@login_required
def create_attendee():
    event_id = request.form.get('eventId')
    event = Event.query.get_or_404(event_id)
    
    # Check if already registered
    existing = Attendee.query.filter_by(
        user_id=current_user.id, 
        event_id=event_id
    ).first()
    
    if existing:
        flash('You are already registered for this event!', 'warning')
        return redirect(url_for('events.profile'))
    
    # Check capacity
    current_attendees = Attendee.query.filter_by(event_id=event_id).count()
    if current_attendees >= event.capacity:
        flash('Sorry, this event is full!', 'danger')
        return redirect(url_for('events.profile'))
    
    # Generate unique token
    token = secrets.token_urlsafe(32)
    
    # Create attendee record first (to get the ID)
    attendee = Attendee(
        user_id=current_user.id,
        event_id=event_id,
        token=token
    )
    
    db.session.add(attendee)
    db.session.flush()  # Get the attendee ID without committing
    
    # Create QR code with attendee information
    qr_data = {
        'attendee_id': attendee.id,
        'user_id': current_user.id,
        'event_id': event_id,
        'token': token,
        'username': current_user.username,
        'event_name': event.title
    }
    
    # Convert to JSON string for QR
    import json
    qr_content = json.dumps(qr_data)
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)
    
    # Create the QR image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR code
    qr_dir = os.path.join(current_app.root_path, 'static', 'qr_codes')
    os.makedirs(qr_dir, exist_ok=True)

    qr_filename = f"qr_{current_user.id}_{event_id}_{attendee.id}.png"
    qr_path = os.path.join(qr_dir, qr_filename)
    
    img.save(qr_path)
    
    # Update attendee with QR path
    attendee.qr_code_path = f'qr_codes/{qr_filename}'
    
    db.session.commit()
    
    flash('Successfully registered for the event!', 'success')
    return redirect(url_for('attendees.registration_success', 
                          attendee_id=attendee.id))

@attendees_blueprint.route('/registration-success/<int:attendee_id>')
@login_required
def registration_success(attendee_id):
    attendee = Attendee.query.get_or_404(attendee_id)
    
    # Security check: only show to the registered user
    if attendee.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('events.profile'))
    
    event = attendee.event
    
    return render_template('registration_success.html', 
                         attendee=attendee, 
                         event=event)

@attendees_blueprint.route('/unregister/<int:event_id>', methods=['POST'])
@login_required
def unregister_attendee(event_id):
    # Find the attendee record
    attendee = Attendee.query.filter_by(
        user_id=current_user.id,
        event_id=event_id
    ).first()
    
    if not attendee:
        flash('You are not registered for this event.', 'warning')
        return redirect(url_for('events.profile'))
    
    # Delete QR code file if it exists
    if attendee.qr_code_path:
        qr_full_path = os.path.join('static', attendee.qr_code_path)
        if os.path.exists(qr_full_path):
            try:
                os.remove(qr_full_path)
            except Exception as e:
                print(f"Error deleting QR code: {e}")
    
    # Delete attendee record
    db.session.delete(attendee)
    db.session.commit()
    
    flash(f'Successfully unregistered from the event!', 'success')
    return redirect(url_for('main.profile'))


@attendees_blueprint.route('/event/<int:event_id>/attendees')
@login_required
def get_attendee(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Get all attendees for this event
    attendees = Attendee.query.filter_by(event_id=event_id).all()
    
    return render_template('attendees_list.html', 
                         event=event, 
                         attendees=attendees)