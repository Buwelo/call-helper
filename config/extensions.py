from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import logging
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()
#login_manager.login_view = 'auth.login'  # Set login route
