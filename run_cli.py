import argparse
import enum
from datetime import datetime, timedelta
from app import db,create_app
from werkzeug.security import generate_password_hash,check_password_hash


app = create_app()

def init_db(args):
    with app.app_context():
        if args.drop:
            print("Dropping all tables...")
            db.drop_all()

        print("Creating tables...")
        db.create_all()
        print("Database Ready!")


def send_reminders(args):
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
            print(f" Reminder: '{e.title}' on {e.date} at {event_time}")

        print("Reminders sent.")


def add_event(args):
    with app.app_context():
        from models.model import Event, EventMode

        try:
            dt = datetime.strptime(args.datetime, "%Y-%m-%d %H:%M:%S")
            event_date = dt.date()
            event_time = dt.time()
        except ValueError:
            print("Invalid datetime format. Use YYYY-MM-DD HH:MM:SS")
            return
        
        try:
            mode = EventMode[args.mode.lower()]
        except KeyError:
            print("Invalid mode. Use online/offline.")
            return

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
        print(f"Event '{args.title}' created successfully!")


def create_user(args):
    with app.app_context():
        from models.model import User

        if User.query.filter((User.username == args.username) | (User.email == args.email)).first():
            print("User already exists.")
            return

        hashed_password = generate_password_hash(args.password)
        new_user = User(username=args.username, email=args.email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()
        print(f"User '{args.username}' created!")


def delete_event(args):
    with app.app_context():
        from models.model import Event
        
        event = Event.query.get(args.id)
        if not event:
            print(" Event not found.")
            return
        
        db.session.delete(event)
        db.session.commit()
        print(f"Event ID {args.id} deleted.")


def delete_user(args):
    with app.app_context():
        from models.model import User
        
        user = User.query.get(args.id)
        if not user:
            print("User not found.")
            return
        
        db.session.delete(user)
        db.session.commit()
        print(f"User ID {args.id} deleted.")


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
    parser_add = subparsers.add_parser("add-event", help="Add event")
    parser_add.add_argument("title")
    parser_add.add_argument("datetime")
    parser_add.add_argument("capacity", type=int)
    parser_add.add_argument("organizer_id", type=int)
    parser_add.add_argument("--mode", default="online")
    parser_add.add_argument("--venue")
    parser_add.add_argument("--description")
    parser_add.set_defaults(func=add_event)

    # create-user
    parser_user = subparsers.add_parser("create-user", help="Create user")
    parser_user.add_argument("username")
    parser_user.add_argument("email")
    parser_user.add_argument("password")
    parser_user.set_defaults(func=create_user)

    # delete-event
    parser_del_event = subparsers.add_parser("delete-event", help="Delete event")
    parser_del_event.add_argument("id", type=int)
    parser_del_event.set_defaults(func=delete_event)

    # delete-user
    parser_del_user = subparsers.add_parser("delete-user", help="Delete user")
    parser_del_user.add_argument("id", type=int)
    parser_del_user.set_defaults(func=delete_user)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
