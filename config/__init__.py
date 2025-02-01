import os
from flask import Flask
from .config import config_dict
from .extensions import db, login_manager, logger, migrate
from routes.auth import auth

def create_app(config_name='development'):
    """Create and configure the app"""
    logger.info(f'Starting app: {config_name}')
    template_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    template_dir = os.path.join(template_dir, 'templates')
    
    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=os.path.join(os.path.dirname(template_dir), 'static')
            )
    app.config.from_object(config_dict[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints
    app.register_blueprint(auth, url_prefix='/auth')
    logger.info(f'App started: {config_name}')
    return app
