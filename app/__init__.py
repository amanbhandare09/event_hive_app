from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text

db = SQLAlchemy()

def create_database_if_not_exists():
    engine = create_engine("mysql+pymysql://root:@localhost")
    db_name = "eventdb"

    with engine.connect() as conn:
        result = conn.execute(text(f"SHOW DATABASES LIKE '{db_name}'")).fetchone()
        if not result:
            conn.execute(text(f"CREATE DATABASE {db_name}"))
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' already exists.")

def create_app():
    app = Flask(__name__)

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/eventdb'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    create_database_if_not_exists()
    db.init_app(app)

    with app.app_context():
        from models.model import Event, User
        db.create_all()
        print("Tables created successfully.")

    return app
