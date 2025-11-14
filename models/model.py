from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import enum
from app import db
from flask_login import UserMixin

# Association table for many-to-many relationshin


# Many-to-many: User attends Event
class Attendee(db.Model):
    __tablename__ = "attendees"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)

    token = db.Column(db.String(255), unique=True, nullable=False)  # Unique token for QR code
    qr_code_path = db.Column(db.String(255))   # Optional: path to QR in static folder
    has_attended = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="attendee_links")
    event = db.relationship("Event", back_populates="attendee_links")


class EventMode(enum.Enum):
    online = "online"
    offline = "offline"


class EventVisibility(enum.Enum):
    public = "public"
    private = "private"


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    venue = db.Column(db.String(150))

    visibility = db.Column(db.Enum(EventVisibility), default=EventVisibility.public, nullable=False)

    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    creator = db.relationship("User", backref=db.backref("created_events", lazy=True))
    description = db.Column(db.Text, nullable=True)
    time = db.Column(db.Time, nullable=False)
    mode = db.Column(db.Enum(EventMode), default=EventMode.offline, nullable=False)
    # capacity = db.Column(db.Integer, nullable=True)  # None means unlimited
    capacity = db.Column(db.Integer, default=0)

    attendee_links = db.relationship("Attendee", back_populates="event", cascade="all, delete")
    attendees = db.relationship('User', secondary='attendees', viewonly=True)


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    attendee_links = db.relationship("Attendee", back_populates="user", cascade="all, delete")