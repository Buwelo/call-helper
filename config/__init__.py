from .config import config_dict
from .extensions import db, login_manager, logger, migrate
import os
from flask import Flask

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
    with app.app_context():
        from routes.auth import auth
        from routes.transcript import transcription
        from routes.analytics import analytics
        app.register_blueprint(auth, url_prefix='/auth')
        app.register_blueprint(transcription, url_prefix='/transcription')
        app.register_blueprint(analytics, url_prefix='/analytics')

    logger.info(f'App started: {config_name}')
    return app