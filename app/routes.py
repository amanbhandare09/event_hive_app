# from connection import db
from flask import Flask, request, jsonify
app = Flask(__name__)


@app.route('/')
def home():
    return "This is Home Page"

# @app.route('/login')
# def login():
#     return "This is Login Page"

@app.route('/register')
def login():
    return "This is Register Page"



@app.route('/create_events', method = 'POST')
def create_events():
    return "Create events"

@app.route('/RSVP')
def event_RSVP():
    return "RSVP events"
