from flask import Flask

from config import Config


def create_app():
    # Create the app
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY
    
    # Register blueprints
    from application.api import api
    app.register_blueprint(api)

    return app