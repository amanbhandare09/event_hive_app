from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import enum 

db = SQLAlchemy()

class eventstatus(enum.Enum):
    online ='online'
    offline='offline'

class event(db.Model):
    __tablename__ = 'events'
    id = db.column(db.Integer,primary_key=True)
    title=db.column(db.String(100),nullable=False)
    date=db.column(db.Date,nullable=False)
    time=db.column(db.Time)
    mode=db.column(db.Enum(eventstatus),default = eventstatus.online,nullable=False)
    venue=db.column(db.string(100),nullable=True)

    def __repr__(self):
        return f"<event {self.title} >"

class Attendee(db.Model):
    __tablename__ ='attendee'
    id = db.column(db.Integer,primary_key=True)
    name = db.column(db.string(100),nullable=False)
    email = db.column(db.string(120),unique=True,nullable=False)
    phone = db.column(db.string(10))
    address=db.column(db.string(200),nullable=False)

    def __repr__(self):
        return f"<Attendee {self.title} >" 
