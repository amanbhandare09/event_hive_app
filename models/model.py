from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import enum 

db = SQLAlchemy()

class eventstatus(enum.Enum):
    online ='online'
    offline='offline'

event_attendee = db.Table(
    'event_attendee',
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True),
    db.Column('attendee_id', db.Integer, db.ForeignKey('attendees.id'), primary_key=True)
)


class event(db.Model):
    __tablename__ = 'events'
    id = db.column(db.Integer,primary_key=True)
    title=db.column(db.String(100),nullable=False)
    date=db.column(db.Date,nullable=False)
    time=db.column(db.Time)
    mode=db.column(db.Enum(eventstatus),default = eventstatus.online,nullable=False)
    venue=db.column(db.string(100),nullable=True)
    
    attendees = db.relationship('Attendee',secondary=event_attendee,back_populates='events')

    def __repr__(self):
        return f"<event {self.title} >"

class Attendee(db.Model):
    __tablename__ ='attendee'
    id = db.column(db.Integer,primary_key=True)
    name = db.column(db.string(100),nullable=False)
    email = db.column(db.string(120),unique=True,nullable=False)
    phone = db.column(db.string(10))
    address=db.column(db.string(200),nullable=False)

    events = db.relationship('Event',secondary=event_attendee,back_populates='attendees')

    def __repr__(self):
        return f"<Attendee {self.title} >" 
