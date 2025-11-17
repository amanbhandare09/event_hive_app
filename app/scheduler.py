from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta  # add timedelta here
from models.model import Event, EventNotification, User
from .email_utils import send_email  # your email function

scheduler = BackgroundScheduler()
# Keep track of notifications sent to avoid duplicates
sent_notifications = set()  # (event_id, user_id)

def notify_users(app):
    """Job to check upcoming events and notify users."""
    with app.app_context():
        now = datetime.now()
        next_day = now + timedelta(days=1)  # Events for the next day

        # Get events happening on next day
        events = Event.query.filter(Event.date == next_day.date()).all()

        for event in events:
            notifications = EventNotification.query.filter_by(event_id=event.id).all()
            
            for notif in notifications:
                key = (event.id, notif.user_id)
                if key in sent_notifications:
                    continue  # already sent

                if not notif.user_id:
                    print(f"Skipping notification: no user_id for event {event.id}")
                    continue

                user = User.query.get(notif.user_id)
                if not user:
                    print(f"Skipping notification: user {notif.user_id} not found")
                    continue

                if not user.email:
                    print(f"Skipping notification: user {user.username} has no email")
                    continue

                subject = f"Reminder: {event.title} is tomorrow!"
                body = f"Hi {user.username},\n\nEvent '{event.title}' starts at {event.starttime} on {event.date}."
                print(f"[Scheduler] Sending email to {user.email}")
                send_email(user.email, subject, body)

                # Mark as sent
                sent_notifications.add(key)

def start_scheduler(app):
    # Run the job every 10 seconds
    scheduler.add_job(func=lambda: notify_users(app), trigger="interval", seconds=10)
    scheduler.start()
    print("[Scheduler] Started, checking for next-day events every 10 seconds.")