from models.user import User
from config.extensions import db, bcrypt
from werkzeug.security import generate_password_hash

def seed_users():
    users = [
        {
            'first_name': 'firstAdmin',
            'last_name': 'lastAdmin',
            'username': 'admin',
            'email': 'admin@example.com',
            'password': bcrypt.generate_password_hash('admin123').decode('utf-8')	
        },
        {
            'first_name': 'firstUser',
            'last_name': 'lastUser',
            'username': 'user',
            'email': 'user@example.com',
            'password': bcrypt.generate_password_hash('user123').decode('utf-8')
        }
    ]

    for user_data in users:
        user = User.query.filter_by(email=user_data['email']).first()
        if not user:
            new_user = User(**user_data)
            db.session.add(new_user)
    
    db.session.commit()

if __name__ == '__main__':
    seed_users()
