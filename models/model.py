from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import enum

db = SQLAlchemy()

class EventStatus(enum.Enum):
    online = 'online'
    offline = 'offline'


# Association table for many-to-many relationship
event_attendee = db.Table(
    'event_attendee',
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True),
    db.Column('attendee_id', db.Integer, db.ForeignKey('attendees.id'), primary_key=True)
)


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time)
    mode = db.Column(db.Enum(EventStatus), default=EventStatus.online, nullable=False)
    venue = db.Column(db.String(100), nullable=True)

    attendees = db.relationship('Attendee', secondary=event_attendee, back_populates='events')

    def __repr__(self):
        return f"<Event {self.title}>"


class Attendee(db.Model):
    __tablename__ = 'attendees'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(10))
    address = db.Column(db.String(200), nullable=False)

    events = db.relationship('Event', secondary=event_attendee, back_populates='attendees')

    def __repr__(self):
        return f"<Attendee {self.name}>"
