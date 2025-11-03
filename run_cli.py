import argparse
import enum
from datetime import datetime, timedelta
from app import db,create_app

app=create_app()



def init_db(args):
    """Initialize or reset the database."""
   
    with app.app_context():
        if args.drop:
            print(" Dropping all tables...")
            db.drop_all()

        print("Creating tables...")
        db.create_all()
        print("Database tables created successfully!")
   


def send_reminders(args):
    """Send reminders for events within the next 24 hours."""
    with app.app_context():
        from models.model import Event

        now = datetime.utcnow()
        next_day = now + timedelta(hours=24)
        events = Event.query.filter(Event.date.between(now.date(), next_day.date())).all()

        if not events:
            print("No events within the next 24 hours.")
            return

        for e in events:
            event_time = e.time.strftime("%H:%M:%S") if e.time else "N/A"
            print(f"Reminder sent for '{e.title}' scheduled on {e.date} at {event_time}")

        print("All reminders simulated successfully!")


def add_event(args):
    """Add an event manually via argparse."""
    with app.app_context():
        from models.model import Event, EventMode

        try:
            # Split datetime into date and time parts
            dt = datetime.strptime(args.datetime, "%Y-%m-%d %H:%M:%S")
            event_date = dt.date()
            event_time = dt.time()
        except ValueError:
            print("Invalid datetime format. Use YYYY-MM-DD HH:MM:SS")
            return

        # Validate mode
        try:
            mode = EventMode[args.mode.lower()]
        except KeyError:
            print("Invalid mode. Use 'online' or 'offline'.")
            return

        # Create and add event
        e = Event(
            title=args.title,
            description=args.description or "",
            date=event_date,
            time=event_time,
            mode=mode,
            venue=args.venue or None,
            capacity=args.capacity,
            organizer_id=args.organizer_id,
        )

        db.session.add(e)
        db.session.commit()
        print(f"Event '{args.title}' added for {event_date} at {event_time}.")


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
    parser_add.add_argument("datetime", type=str, help="Event date and time (format: YYYY-MM-DD HH:MM:SS)")
    parser_add.add_argument("capacity", type=int, help="Event capacity")
    parser_add.add_argument("organizer_id", type=int, help="Organizer user ID")
    parser_add.add_argument("--mode", type=str, default="online", help="Event mode: online or offline")
    parser_add.add_argument("--venue", type=str, help="Venue for offline events")
    parser_add.add_argument("--description", type=str, help="Optional event description")
    parser_add.set_defaults(func=add_event)

    args = parser.parse_args()

    # Handle no command case
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()