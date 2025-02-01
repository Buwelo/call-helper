# **Flask Web Application**

This is a Flask-based web application using **Flask-SQLAlchemy** for database management, **Flask-Login** for user authentication, and **Flask-Migrate** for handling database migrations.

## **Prerequisites**

Before running the app, ensure you have the following installed:

- **Python 3.x** (preferably the latest version)
- **pip** (Python's package installer)
- **PostgreSQL** or any other database of your choice

## **Setup and Installation**

1. **Clone the repository**:

    ```bash
    git clone https://github.com/your_username/your-flask-app.git
    cd your-flask-app
    ```

2. **Create and activate a virtual environment**:

    - For **macOS/Linux**:
    
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

    - For **Windows**:
    
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

## **Configuration**

### **Create the `.env` File**

Create a `.env` file in the root directory of the project (if it doesn’t exist) and add your environment-specific configurations, such as the database URL and Flask secret key.

Example `.env` file:


- **SECRET_KEY**: Used to secure session data and other cryptographic operations.
- **DATABASE_URL**: The connection string for your PostgreSQL database (replace `username`, `password`, and `db_name` with your actual database credentials).
- **FLASK_ENV**: Set this to `development` for local development or `production` for deployment.

### **Add `.env` to `.gitignore**

To prevent the `.env` file from being tracked by Git, add `.env` to your `.gitignore` file:


## **Running the Application**

### **1. Set the Flask environment variables**:

- For **macOS/Linux**:

    ```bash
    export FLASK_APP=app.py
    export FLASK_ENV=development  # Use 'production' for production environment
    ```

- For **Windows**:

    ```bash
    set FLASK_APP=app.py
    set FLASK_ENV=development
    ```
### **2. Run migration**:

```bash
flask db upgrade
 ```

### **3. Run the Flask application**:

```bash
flask run
 ```
### **4. Run seeder**:

```bash
flask shell
from seeders.userSeeder import seed_users
seed_users()
 ```
