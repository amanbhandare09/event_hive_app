from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import enum
from app import db
from flask_login import UserMixin

# Association table for many-to-many relationship
event_attendees = db.Table(
    "event_attendees",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("event_id", db.Integer, db.ForeignKey("events.id"), primary_key=True)
)

class EventMode(enum.Enum):
    online = "online"
    offline = "offline"

class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time)
    mode = db.Column(db.Enum(EventMode), default=EventMode.online, nullable=False)
    venue = db.Column(db.String(150))
    capacity = db.Column(db.Integer, default=100)

    # Link to creator (User)
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    creator = db.relationship("User", backref=db.backref("created_events", lazy=True))

    attendees = db.relationship(
        "User", secondary=event_attendees, back_populates="attending_events"
    )

    def __repr__(self):
        return f"<Event {self.title}>"
    

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Many-to-many: user can attend multiple events
    attending_events = db.relationship(
        "Event", secondary=event_attendees, back_populates="attendees"
    )

    def __repr__(self):
        return f"<User {self.username}>"
