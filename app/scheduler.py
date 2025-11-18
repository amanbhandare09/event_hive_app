# scheduler.py (or scheduler.html → rename to .py if not already)
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from models.model import Event, EventNotification, User
from .email_utils import send_email
import os

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


# ============================================
# NEW: AUTO-ARCHIVE COMPLETED EVENTS (ADDED ONLY)
# ============================================
def archive_completed_events(app):
    """Automatically archive events after their end time has passed"""
    with app.app_context():
        from app import db
        from flask import current_app
        
        now = datetime.now()
        current_date = now.date()
        current_time = now.time()

        completed_events = Event.query.filter(
            Event.is_archived == False,
            db.or_(
                Event.date < current_date,
                db.and_(
                    Event.date == current_date,
                    Event.endtime != None,
                    Event.endtime < current_time
                )
            )
        ).all()

        if not completed_events:
            return

        print(f"[Scheduler] Auto-archiving {len(completed_events)} completed event(s)")

        for event in completed_events:
            print(f"[Scheduler] Archiving event: {event.title} (ID: {event.id})")
            event.is_archived = True

            # Clean up attendees and QR codes
            event.attendees.clear()
            for attendee in event.attendee_links:
                if attendee.qr_code_path:
                    qr_path = os.path.join(current_app.root_path, "static", attendee.qr_code_path)
                    if os.path.exists(qr_path):
                        try:
                            os.remove(qr_path)
                        except:
                            pass
                db.session.delete(attendee)

        db.session.commit()
        print(f"[Scheduler] Successfully archived {len(completed_events)} event(s)")


def start_scheduler(app):
    """
    Start the background scheduler with all jobs.
    """
    # Job 1: Notify users about next-day events (every 10 seconds) → UNCHANGED
    scheduler.add_job(
        func=lambda: notify_users(app), 
        trigger="interval", 
        seconds=10,
        id='notify_users',
        name='Notify users about upcoming events',
        replace_existing=True
    )
    print("[Scheduler] Job 1: Email notifications - every 10 seconds")
    
    # NEW JOB: Auto-archive completed events (every hour) → ONLY ADDITION
    scheduler.add_job(
        func=lambda: archive_completed_events(app),
        trigger="interval",
        minutes=5,
        id='auto_archive_events',
        name='Auto-archive completed events',
        replace_existing=True
    )
    print("[Scheduler] Job 2: Auto-archive events - every 5 minutes")
    
    # Start the scheduler
    scheduler.start()
    print("[Scheduler] Background scheduler started successfully!")
    
    # Optional: Run auto-archive immediately on startup
    print("[Scheduler] Running initial auto-archive check...")
    archive_completed_events(app)