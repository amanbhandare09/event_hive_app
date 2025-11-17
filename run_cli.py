import argparse
import enum
from datetime import datetime, timedelta
from app import db, create_app
from werkzeug.security import generate_password_hash

app = create_app()

# ---------------------------------------------------------
# INIT-DB
# ---------------------------------------------------------
def init_db(args):
    """Initialize or reset the database."""
    with app.app_context():
        if args.drop:
            print("Dropping all tables...")
            db.drop_all()

        print("Creating tables...")
        db.create_all()
        print("Database tables created successfully!")

# ---------------------------------------------------------
# SEND REMINDERS
# ---------------------------------------------------------
def send_reminders(args):
    with app.app_context():
        from models.model import Event

        now = datetime.utcnow()
        next_day = now + timedelta(hours=24)

        events = Event.query.filter(
            Event.date.between(now.date(), next_day.date())
        ).all()

        if not events:
            print("No events within the next 24 hours.")
            return

        for e in events:
            if e.starttime:
                time_str = e.starttime.strftime("%H:%M")
                if e.endtime:
                    time_str += f" - {e.endtime.strftime('%H:%M')}"
            else:
                time_str = "N/A"

            print(
                f"Reminder: '{e.title}' on {e.date} at {time_str} | "
                f"Mode: {e.mode.value} | Visibility: {e.visibility.value}"
            )

        print(f"{len(events)} reminder(s) sent successfully!")

# ---------------------------------------------------------
# ADD EVENT
# ---------------------------------------------------------
def add_event(args):
    """Add a new event."""
    with app.app_context():
        from models.model import Event, EventMode, EventVisibility, Eventtag

        try:
            event_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")
            return

        start_time = None
        end_time = None
        if args.starttime:
            try:
                start_time = datetime.strptime(args.starttime, "%H:%M:%S").time()
            except ValueError:
                print("Invalid start time format. Use HH:MM:SS")
                return
        if args.endtime:
            try:
                end_time = datetime.strptime(args.endtime, "%H:%M:%S").time()
            except ValueError:
                print("Invalid end time format. Use HH:MM:SS")
                return

        try:
            mode = EventMode[args.mode.lower()]
        except KeyError:
            print("Invalid mode. Use online/offline.")
            return

        try:
            visibility = EventVisibility[args.visibility.lower()]
        except KeyError:
            print("Invalid visibility. Use 'public' or 'private'.")
            return

        try:
            tag = Eventtag[args.tags.upper()]
        except KeyError:
            print("Invalid tag. Available tags:")
            for t in Eventtag:
                print(f" - {t.name} ({t.value})")
            return

        event = Event(
            title=args.title,
            description=args.description or "",
            date=event_date,
            starttime=start_time,
            endtime=end_time,
            mode=mode,
            venue=args.venue or None,
            capacity=args.capacity,
            tags=tag,
            visibility=visibility,
            organizer_id=args.organizer_id,
        )

        db.session.add(event)
        db.session.commit()
        print(f"Event '{args.title}' created on {event_date} | Mode: {mode.value} | Tag: {tag.value}")

# ---------------------------------------------------------
# CREATE USER
# ---------------------------------------------------------
def create_user(args):
    """Create a new user."""
    with app.app_context():
        from models.model import User

        if User.query.filter((User.username == args.username) | (User.email == args.email)).first():
            print("User already exists.")
            return

        hashed_password = generate_password_hash(args.password)
        user = User(username=args.username, email=args.email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        print(f"User '{args.username}' created successfully with email '{args.email}'!")

# ---------------------------------------------------------
# LIST EVENTS
# ---------------------------------------------------------
def list_events(args):
    """List all events or filter by visibility."""
    with app.app_context():
        from models.model import Event, EventVisibility

        query = Event.query
        if args.visibility:
            try:
                vis = EventVisibility[args.visibility.lower()]
                query = query.filter_by(visibility=vis)
            except KeyError:
                print("Invalid visibility. Use 'public' or 'private'.")
                return

        events = query.all()
        if not events:
            print("No events found.")
            return

        print(f"\nFound {len(events)} event(s):\n")
        for e in events:
            time_str = e.starttime.strftime("%H:%M") if e.starttime else "N/A"
            if e.starttime and e.endtime:
                time_str += f" - {e.endtime.strftime('%H:%M')}"
            print(f"  ID: {e.id} | {e.title}")
            print(f"    Date: {e.date} | Time: {time_str}")
            print(f"    Mode: {e.mode.value} | Visibility: {e.visibility.value} | Tag: {e.tags.value}")
            print(f"    Capacity: {e.capacity} | Venue: {e.venue or 'N/A'}\n")

# ---------------------------------------------------------
# UPDATE EVENT
# ---------------------------------------------------------
def update_event(args):
    with app.app_context():
        from models.model import Event, EventMode, EventVisibility, Eventtag

        event = Event.query.get(args.event_id)
        if not event:
            print(f"No event found with ID {args.event_id}")
            return

        if args.title:
            event.title = args.title
        if args.date:
            try:
                event.date = datetime.strptime(args.date, "%Y-%m-%d").date()
            except ValueError:
                print("Invalid date format. Use YYYY-MM-DD")
                return
        if args.starttime:
            try:
                event.starttime = datetime.strptime(args.starttime, "%H:%M:%S").time()
            except ValueError:
                print("Invalid start time format. Use HH:MM:SS")
                return
        if args.endtime:
            try:
                event.endtime = datetime.strptime(args.endtime, "%H:%M:%S").time()
            except ValueError:
                print("Invalid end time format. Use HH:MM:SS")
                return
        if args.mode:
            try:
                event.mode = EventMode[args.mode.lower()]
            except KeyError:
                print("Invalid mode. Use 'online' or 'offline'")
                return
        if args.visibility:
            try:
                event.visibility = EventVisibility[args.visibility.lower()]
            except KeyError:
                print("Invalid visibility. Use 'public' or 'private'")
                return
        if args.capacity:
            event.capacity = args.capacity
        if args.venue:
            event.venue = args.venue
        if args.description:
            event.description = args.description
        if args.tags:
            try:
                event.tags = Eventtag[args.tags.upper()]
            except KeyError:
                print("Invalid tag.")
                return

        db.session.commit()
        print(f"Event '{event.title}' (ID {event.id}) updated successfully!")

# ---------------------------------------------------------
# DELETE EVENT
# ---------------------------------------------------------
def delete_event(args):
    with app.app_context():
        from models.model import Event

        event = Event.query.get(args.event_id)
        if not event:
            print(f"No event found with ID {args.event_id}")
            return
        db.session.delete(event)
        db.session.commit()
        print(f"Event '{event.title}' (ID {args.event_id}) deleted successfully!")

# ---------------------------------------------------------
# VIEW ATTENDEES
# ---------------------------------------------------------
def view_attendees(args):
    with app.app_context():
        from models.model import Event

        event = Event.query.get(args.event_id)
        if not event:
            print(f"No event found with ID {args.event_id}")
            return
        if not event.attendees:
            print(f"No attendees registered for '{event.title}'")
            return

        print(f"Attendees for '{event.title}':")
        for user in event.attendees:
            print(f" - {user.username} ({user.email})")

# ---------------------------------------------------------
# DELETE USER
# ---------------------------------------------------------
def delete_user(args):
    with app.app_context():
        from models.model import User

        user = User.query.get(args.user_id)
        if not user:
            print(f"No user found with ID {args.user_id}")
            return
        db.session.delete(user)
        db.session.commit()
        print(f"User '{user.username}' (ID {user.id}) deleted successfully!")

# ---------------------------------------------------------
# SEND EMAIL NOTIFICATION
# ---------------------------------------------------------
def send_event_email(args):
    """Send email to all attendees of an event"""
    with app.app_context():
        from models.model import Event
        from app.email_utils import send_email  # Your email sending function

        event = Event.query.get(args.event_id)
        if not event:
            print(f"No event found with ID {args.event_id}")
            return
        if not event.attendees:
            print(f"No attendees to send emails to for '{event.title}'")
            return

        subject = f"Reminder: {event.title}"
        body = f"Hello,\n\nThis is a reminder for the event '{event.title}' on {event.date}."

        for user in event.attendees:
            send_email(user.email, subject, body)
            print(f"Email sent to {user.email}")

        print("All emails sent successfully!")
# ---------------------------------------------------------
# LIST USERS
# ---------------------------------------------------------
def list_users(args):
    """List all registered users."""
    with app.app_context():
        from models.model import User

        users = User.query.all()
        if not users:
            print("No users found.")
            return

        print(f"\nFound {len(users)} user(s):\n")
        for u in users:
            print(f"  ID: {u.id} | Username: {u.username} | Email: {u.email}")

# ---------------------------------------------------------
# MAIN & ARGUMENT PARSER
# ---------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Event Hive CLI")
    subparsers = parser.add_subparsers()

    # init-db
    parser_init = subparsers.add_parser("init-db", help="Initialize database")
    parser_init.add_argument("--drop", action="store_true", help="Drop tables first")
    parser_init.set_defaults(func=init_db)

    # send-reminders
    parser_rem = subparsers.add_parser("send-reminders", help="Send reminders")
    parser_rem.set_defaults(func=send_reminders)

    # add-event
    parser_add = subparsers.add_parser("add-event", help="Add a new event manually")
    parser_add.add_argument("title", type=str, help="Title of the event")
    parser_add.add_argument("date", type=str, help="Event date (YYYY-MM-DD)")
    parser_add.add_argument("capacity", type=int, help="Event capacity")
    parser_add.add_argument("organizer_id", type=int, help="Organizer user ID")
    parser_add.add_argument("--mode", type=str, default="online", help="Event mode: online/offline")
    parser_add.add_argument("--venue", type=str, help="Event venue")
    parser_add.add_argument("--description", type=str, help="Event description")
    parser_add.add_argument("--starttime", type=str, help="Start time (HH:MM:SS)")
    parser_add.add_argument("--endtime", type=str, help="End time (HH:MM:SS)")
    parser_add.add_argument("--visibility", type=str, default="public", help="Event visibility: public/private")
    parser_add.add_argument("--tags", type=str, default="CELEBRATION", help="Event tag (e.g., WORKSHOP, PARTY)")
    parser_add.set_defaults(func=add_event)

    # create-user
    parser_user = subparsers.add_parser("create-user", help="Create a new user")
    parser_user.add_argument("username", type=str, help="Username")
    parser_user.add_argument("email", type=str, help="Email")
    parser_user.add_argument("password", type=str, help="Password")
    parser_user.set_defaults(func=create_user)

    # list-events
    parser_list = subparsers.add_parser("list-events", help="List all events")
    parser_list.add_argument("--visibility", type=str, help="Filter: public/private")
    parser_list.set_defaults(func=list_events)

    # update-event
    parser_update = subparsers.add_parser("update-event", help="Update an event")
    parser_update.add_argument("event_id", type=int, help="Event ID")
    parser_update.add_argument("--title", type=str)
    parser_update.add_argument("--date", type=str)
    parser_update.add_argument("--starttime", type=str)
    parser_update.add_argument("--endtime", type=str)
    parser_update.add_argument("--mode", type=str)
    parser_update.add_argument("--visibility", type=str)
    parser_update.add_argument("--capacity", type=int)
    parser_update.add_argument("--venue", type=str)
    parser_update.add_argument("--description", type=str)
    parser_update.add_argument("--tags", type=str)
    parser_update.set_defaults(func=update_event)

    # delete-event
    parser_delete = subparsers.add_parser("delete-event", help="Delete an event")
    parser_delete.add_argument("event_id", type=int, help="Event ID")
    parser_delete.set_defaults(func=delete_event)

    # view-attendees
    parser_attendees = subparsers.add_parser("view-attendees", help="View attendees of an event")
    parser_attendees.add_argument("event_id", type=int, help="Event ID")
    parser_attendees.set_defaults(func=view_attendees)

    # delete-user
    parser_delete_user = subparsers.add_parser("delete-user", help="Delete a user")
    parser_delete_user.add_argument("user_id", type=int, help="User ID")
    parser_delete_user.set_defaults(func=delete_user)

    # send-email
    parser_email = subparsers.add_parser("send-email", help="Send email notification for an event")
    parser_email.add_argument("event_id", type=int, help="Event ID")
    parser_email.set_defaults(func=send_event_email)

    # list-users
    parser_list_users = subparsers.add_parser("list-users", help="List all users")
    parser_list_users.set_defaults(func=list_users)


    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
