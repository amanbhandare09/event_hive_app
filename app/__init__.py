from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Database configuration
    app.config['SECRET_KEY'] = '91ba96dbf66221f753176c6a80f0e7905444d410630b70f89445e7281d0001aa'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

    db.init_app(app)

    from .main import main_blueprint
    app.register_blueprint(main_blueprint)
    
    from .auth import auth_blueprint
    app.register_blueprint(auth_blueprint)

    return app
