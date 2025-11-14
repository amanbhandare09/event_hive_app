from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import enum
from app import db
from flask_login import UserMixin


# ============================================================
# ENUMS
# ============================================================

class EventMode(enum.Enum):
    online = "online"
    offline = "offline"


class EventVisibility(enum.Enum):
    public = "public"
    private = "private"


class Eventtag(enum.Enum):
    WORKSHOP = "Workshop"
    SEMINAR = "Seminar"
    MEETING = "Meeting"
    CONFERENCE = "Conference"
    PARTY = "Party"
    CELEBRATION = "Celebration"
    NETWORKING = "Networking"
    FUNDRAISER = "Fundraiser"
    COMPETITION = "Competition"
    PERFORMANCE = "Performance"
    FESTIVAL = "Festival"
    WEBINAR = "Webinar"
    TRAINING = "Training"
    SPORTS = "Sports"
    TRIP = "Trip"
    VOLUNTEERING = "Volunteering"
    HACKATHON = "Hackathon"
    LAUNCH = "Launch"
    CULTURAL = "Cultural"
    EDUCATIONAL = "Educational"
    ENTERTAINMENT = "Entertainment"
    SOCIAL = "Social"
    PROFESSIONAL = "Professional"
    TECH = "Tech"
    ART = "Art"
    MUSIC = "Music"
    FOOD = "Food"
    HEALTH = "Health"
    ENVIRONMENT = "Environment"


# ============================================================
# ATTENDEE TABLE (replaces event_attendees)
# ============================================================

class Attendee(db.Model):
    __tablename__ = "attendees"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)

    # From second model
    token = db.Column(db.String(255), unique=True, nullable=False)  
    qr_code_path = db.Column(db.String(255))   
    has_attended = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="attendee_links")
    event = db.relationship("Event", back_populates="attendee_links")


# ============================================================
# EVENT MODEL (fully merged)
# ============================================================

class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)

    # From BOTH models
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    # Date + Time (merged: including single time OR start+end)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time)        # from second model
    starttime = db.Column(db.Time)   # from first model
    endtime = db.Column(db.Time)     # from first model

    # Mode and Venue
    mode = db.Column(db.Enum(EventMode), default=EventMode.online, nullable=False)
    venue = db.Column(db.String(150))

    # Capacity + Tags + Visibility
    capacity = db.Column(db.Integer, default=100)
    tags = db.Column(db.Enum(Eventtag), default=Eventtag.CELEBRATION, nullable=False)
    visibility = db.Column(db.Enum(EventVisibility), default=EventVisibility.public, nullable=False)

    # Organizer
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    creator = db.relationship("User", backref=db.backref("created_events", lazy=True))

    # Attendee relationships
    attendee_links = db.relationship("Attendee", back_populates="event", cascade="all, delete")
    attendees = db.relationship("User", secondary="attendees", viewonly=True)

    def __repr__(self):
        return f"<Event {self.title}, Visibility={self.visibility.value}>"


# ============================================================
# USER MODEL (fully merged)
# ============================================================

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # From second model
    attendee_links = db.relationship("Attendee", back_populates="user", cascade="all, delete")

    # View-only attending events
    attending_events = db.relationship(
        "Event", secondary="attendees", viewonly=True
    )

    def __repr__(self):
        return f"<User {self.username}>"
