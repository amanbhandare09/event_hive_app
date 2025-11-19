from flask import Flask, app, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate



login_manager = LoginManager()

db = SQLAlchemy()

migrate = Migrate()

def create_app():
    app = Flask(__name__)

    DB_URI = "mysql+pymysql://admin:eventhive25@eventhive-db.cf2u4ey4ohk5.ap-south-1.rds.amazonaws.com:3306/eventhive_mysql"
    
    app.config['SECRET_KEY'] = '91ba96dbf66221f753176c6a80f0e7905444d410630b70f89445e7281d0001aa'
    app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI          # ← fixed the missing "A" in SQLALCHEMY
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False     # ← prevents warnings + helps stability

    # Add these 3 lines for reliable RDS connection (very important for AWS)
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 3600,
    'connect_args': {
        'ssl': {'ssl-mode': 'REQUIRED'}   # ← THIS IS THE CORRECT PyMySQL WAY
        }
    }

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)

    from models.model import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # After creating the Flask app
    # @app.errorhandler(404)
    # def page_not_found(e):
    #     return render_template('errors/404.html'), 404

    from .main import main_blueprint
    app.register_blueprint(main_blueprint)
    
    from .auth import auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .main import events_blueprint, attendees_blueprint
    app.register_blueprint(events_blueprint)
    app.register_blueprint(attendees_blueprint)
    
    # Start scheduler AFTER app is ready
    from .scheduler import start_scheduler
    start_scheduler(app)

    return app

if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)