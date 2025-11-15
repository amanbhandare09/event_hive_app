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
    """Send reminders for events within the next 24 hours."""
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
            # Build readable time string
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
    """Add an event manually via argparse."""
    with app.app_context():
        from models.model import Event, EventMode, EventVisibility, Eventtag

        # Parse date
        try:
            event_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")
            return

        # Parse time fields
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

        # Validate mode
        try:
            mode = EventMode[args.mode.lower()]
        except KeyError:
            print("Invalid mode. Use 'online' or 'offline'.")
            return

        # Validate visibility
        try:
            visibility = EventVisibility[args.visibility.lower()]
        except KeyError:
            print("Invalid visibility. Use 'public' or 'private'.")
            return

        # Validate tags
        try:
            tag = Eventtag[args.tags.upper()]
        except KeyError:
            print("Invalid tag. Available tags:")
            for t in Eventtag:
                print(f" - {t.name} ({t.value})")
            return

        # Create event
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
    """Create a new user account."""
    with app.app_context():
        from models.model import User

        existing_user = User.query.filter(
            (User.username == args.username) | (User.email == args.email)
        ).first()

        if existing_user:
            print("User with this username or email already exists.")
            return

        hashed_password = generate_password_hash(args.password)

        user = User(
            username=args.username,
            email=args.email,
            password=hashed_password
        )

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
            # Build time string
            if e.starttime:
                time_str = e.starttime.strftime("%H:%M")
                if e.endtime:
                    time_str += f" - {e.endtime.strftime('%H:%M')}"
            else:
                time_str = "N/A"

            print(f"  ID: {e.id} | {e.title}")
            print(f"    Date: {e.date} | Time: {time_str}")
            print(f"    Mode: {e.mode.value} | Visibility: {e.visibility.value} | Tag: {e.tags.value}")
            print(f"    Capacity: {e.capacity} | Venue: {e.venue or 'N/A'}\n")


# ---------------------------------------------------------
# MAIN & ARGUMENT PARSER
# ---------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Manage your Flask Event App")
    subparsers = parser.add_subparsers(help="Available commands")

    # init-db
    parser_init = subparsers.add_parser("init-db", help="Initialize the database")
    parser_init.add_argument("--drop", action="store_true", help="Drop existing tables before creating new ones")
    parser_init.set_defaults(func=init_db)

    # send-reminders
    parser_reminders = subparsers.add_parser("send-reminders", help="Send event reminders within 24 hours")
    parser_reminders.set_defaults(func=send_reminders)

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

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
