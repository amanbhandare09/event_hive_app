# app/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from models.model import Event, EventNotification, User
from .email_utils import send_email
import os

scheduler = BackgroundScheduler()
sent_notifications = set()  # (event_id, user_id)


# ────────────────────── NOTIFY USERS (SAFE) ──────────────────────
def notify_users(app):
    with app.app_context():
        try:
            now = datetime.now()
            next_day = now + timedelta(days=1)

            events = Event.query.filter(Event.date == next_day.date()).all()

            for event in events:
                notifications = EventNotification.query.filter_by(event_id=event.id).all()
                for notif in notifications:
                    key = (event.id, notif.user_id)
                    if key in sent_notifications:
                        continue

                    user = User.query.get(notif.user_id)
                    if not user or not user.email:
                        continue

                    subject = f"Reminder: {event.title} is tomorrow!"
                    body = f"Hi {user.username},\n\nEvent '{event.title}' starts at {event.starttime} on {event.date}."
                    print(f"[Scheduler] Sending email to {user.email}")
                    send_email(user.email, subject, body)
                    sent_notifications.add(key)

        except Exception as e:
            if "no such table" in str(e).lower() or "relation" in str(e).lower():
                print("[Scheduler] DB not ready yet (notify_users) – skipping")
            # else: print(f"[Scheduler] Notification error: {e}")  # optional
            return  # silently skip until DB exists


# ────────────────────── AUTO-ARCHIVE (ALREADY SAFE) ──────────────────────
def archive_completed_events(app):
    with app.app_context():
        from app import db
        from flask import current_app
        
        try:
            now = datetime.now()
            current_date = now.date()
            current_time = now.time()

            completed_events = Event.query.filter(
                Event.is_archived == False,
                db.or_(
                    Event.date < current_date,
                    db.and_(
                        Event.date == current_date,
                        Event.endtime.isnot(None),
                        Event.endtime < current_time
                    )
                )
            ).all()

            if not completed_events:
                return

            print(f"[Scheduler] Auto-archiving {len(completed_events)} event(s)")
            for event in completed_events:
                print(f"[Scheduler] Archiving: {event.title} (ID: {event.id})")
                event.is_archived = True
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

        except Exception as e:
            if "no such table" in str(e).lower():
                print("[Scheduler] DB not ready yet (auto-archive) – skipping")
            return


# ────────────────────── START SCHEDULER ──────────────────────
def start_scheduler(app):
    scheduler.add_job(
        func=lambda: notify_users(app),
        trigger="interval",
        minutes=5,
        id='notify_users',
        replace_existing=True
    )
    print("[Scheduler] Job 1: Email notifications - every 5 minutes")
    scheduler.add_job(
        func=lambda: archive_completed_events(app),
        trigger="interval",
        minutes=5,          # ← you wanted fast archiving
        id='auto_archive_events',
        replace_existing=True
    )
    print("[Scheduler] Job 2: Auto-archive events - every 5 minutes")

    scheduler.start()
    print("[Scheduler] Background scheduler started successfully!")
    
    # Safe initial run
    archive_completed_events(app)