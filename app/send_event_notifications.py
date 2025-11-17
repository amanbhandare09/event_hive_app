# send_event_notifications.py
from datetime import datetime, timedelta
from app import create_app, db
from app.models import Event, EventNotification, User
from app.email_utils import send_email

app = create_app()

with app.app_context():
    tomorrow = datetime.utcnow() + timedelta(days=1)
    start = datetime(tomorrow.year, tomorrow.month, tomorrow.day)
    end = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 23, 59, 59)

    events = Event.query.filter(Event.date >= start, Event.date <= end).all()

    for event in events:
        notifications = EventNotification.query.filter_by(event_id=event.id).all()
        for notif in notifications:
            user = User.query.get(notif.user_id)
            subject = f"Reminder: {event.title} is tomorrow!"
            body = f"""
            <p>Hi {user.username},</p>
            <p>This is a reminder that the event <strong>{event.title}</strong> is happening tomorrow.</p>
            <p>Date: {event.date.strftime('%d %b %Y')}</p>
            <p>Time: {event.starttime.strftime('%I:%M %p')} - {event.endtime.strftime('%I:%M %p')}</p>
            <p>Location: {event.venue}</p>
            """
            send_email(user.email, subject, body)
