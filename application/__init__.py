from flask import Flask


def create_app():
    # Create the app
    app = Flask(__name__)
    
    # Register blueprints
    from application.api import api
    app.register_blueprint(api)

    return app