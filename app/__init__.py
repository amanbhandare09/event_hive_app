from flask import Flask, app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate



login_manager = LoginManager()

db = SQLAlchemy()

migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Database configuration
    app.config['SECRET_KEY'] = '91ba96dbf66221f753176c6a80f0e7905444d410630b70f89445e7281d0001aa'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)

    from models.model import User

    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .main import main_blueprint
    app.register_blueprint(main_blueprint)
    
    from .auth import auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .main import events_blueprint, attendees_blueprint
    app.register_blueprint(events_blueprint)
    app.register_blueprint(attendees_blueprint)

    return app
