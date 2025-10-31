from app import create_app, db
from models.model import User, Event

app = create_app()

def init_db():
    """Initialize the database."""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

def drop_db():
    """Drop all database tables."""
    with app.app_context():
        db.drop_all()
        print("All database tables dropped!")

def reset_db():
    """Drop and recreate all database tables."""
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset successfully!")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python manage.py [init|drop|reset]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'init':
        init_db()
    elif command == 'drop':
        drop_db()
    elif command == 'reset':
        reset_db()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: init, drop, reset")