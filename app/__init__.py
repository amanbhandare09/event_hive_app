from flask import Flask

def create_app():
    app = Flask(__name__)

    from.main import main_blueprint
    app.register_blueprint(main_blueprint)
    from.auth import auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    return app