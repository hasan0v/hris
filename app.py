import os
import os # Re-add os import if needed elsewhere, was removed by previous change
from flask import Flask, request # Keep request if needed elsewhere
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
# from flask_babel import Babel # Removed
# from flask_migrate import Migrate # Removed
from config import Config # Import configuration (Changed to absolute)

# Initialize extensions
db = SQLAlchemy()
# migrate = Migrate() # Removed
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
socketio = SocketIO()
# babel = Babel() # Removed: Initialize Babel

# Import models *after* db is defined to avoid circular imports
import models # Models are now defined (Changed to absolute)

# App factory pattern could be considered later if complexity grows
app = Flask(__name__)

# Load configuration
app.config.from_object(Config)

# Initialize extensions with the app instance
db.init_app(app)
# migrate.init_app(app, db) # Removed
login_manager.init_app(app)
socketio.init_app(app)
# babel.init_app(app) # Removed: Initialize Babel with app

# Register blueprints/routes
from auth import auth_bp # Import the auth blueprint
from hr import hr_bp     # Import the hr blueprint
from applicant import applicant_bp # Import the applicant blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(hr_bp)
app.register_blueprint(applicant_bp)

# --- SocketIO Event Handlers ---
from flask_socketio import join_room, leave_room
from flask_login import current_user

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        user_room = f'user_{current_user.id}'
        join_room(user_room)
        print(f'Socket connected: User {current_user.id} joined room {user_room}')
    else:
        print('Socket connected: Anonymous user')

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        user_room = f'user_{current_user.id}'
        leave_room(user_room)
        print(f'Socket disconnected: User {current_user.id} left room {user_room}')
    else:
        print('Socket disconnected: Anonymous user')
# --- End SocketIO Event Handlers ---

# --- Babel Locale Selector - Removed ---

@app.route('/')
def index():
    # Fetch all vacancies to display on the main page
    # Add filtering for "active" vacancies later if needed
    vacancies = models.Vacancy.query.order_by(models.Vacancy.created_at.desc()).all()
    from flask import render_template
    return render_template('index.html', vacancies=vacancies)

# --- User Loader for Flask-Login ---
@login_manager.user_loader
def load_user(user_id):
    # Return the user object from the user ID stored in the session
    return db.session.get(models.User, int(user_id))
# --- End User Loader ---

# --- Template Context Processor ---
@app.context_processor
def inject_enums():
    # Make Enums available in all templates
    return dict(UserRole=models.UserRole, ApplicationStatus=models.ApplicationStatus)
# --- End Context Processor ---

# --- Database Initialization Command ---
@app.cli.command('create-db')
def create_db():
    """Drops and recreates the database tables."""
    with app.app_context():
        print("Dropping existing tables...")
        db.drop_all()
        print("Creating new tables...")
        db.create_all()
    print('Database tables recreated!')
# --- End Database Initialization Command ---

# --- Sass Compilation Command ---
@app.cli.command('compile-sass')
def compile_sass():
    """Compiles static/scss/style.scss to static/css/style.css"""
    try:
        import sass
        print("Compiling Sass...")
        sass_dir = os.path.join(app.static_folder, 'scss')
        css_dir = os.path.join(app.static_folder, 'css')
        input_file = os.path.join(sass_dir, 'style.scss')
        output_file = os.path.join(css_dir, 'style.css')

        if not os.path.exists(css_dir):
            os.makedirs(css_dir)

        if os.path.exists(input_file):
            compiled_css = sass.compile(filename=input_file, output_style='compressed')
            with open(output_file, 'w') as f:
                f.write(compiled_css)
            print(f"Successfully compiled {input_file} to {output_file}")
        else:
            print(f"Error: Input file not found at {input_file}")

    except ImportError:
        print("Error: 'libsass' package not found. Please install it (`pip install libsass`)")
    except Exception as e:
        print(f"Error during Sass compilation: {e}")
# --- End Sass Compilation Command ---

# --- Uploads Cleanup Command ---
import click
from datetime import datetime, timedelta

@app.cli.command('cleanup-uploads')
@click.option('--days', default=1, type=int, help='Delete files older than this many days.')
def cleanup_uploads(days):
    """Deletes files in the upload folder older than specified days."""
    upload_path = app.config.get('UPLOAD_PATH')
    if not upload_path or not os.path.exists(upload_path):
        print(f"Upload path '{upload_path}' not found or not configured.")
        return

    cutoff = datetime.now() - timedelta(days=days)
    print(f"Scanning '{upload_path}' for files older than {days} day(s) ({cutoff.strftime('%Y-%m-%d %H:%M:%S')})...")
    deleted_count = 0
    error_count = 0

    for filename in os.listdir(upload_path):
        filepath = os.path.join(upload_path, filename)
        if os.path.isfile(filepath):
            try:
                file_mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_mod_time < cutoff:
                    os.remove(filepath)
                    print(f"Deleted: {filename} (Modified: {file_mod_time.strftime('%Y-%m-%d %H:%M:%S')})")
                    deleted_count += 1
            except Exception as e:
                print(f"Error deleting {filename}: {e}")
                error_count += 1

    print(f"Cleanup complete. Deleted {deleted_count} files. Encountered {error_count} errors.")
# --- End Uploads Cleanup Command ---


if __name__ == '__main__':
    # Debug is controlled by FLASK_DEBUG env var set in docker-compose
    # Port is handled by docker-compose port mapping
    # Use Flask's built-in run command via 'flask run' or python app.py
    # The CMD in Dockerfile handles running the app
    # Use socketio.run for development if running directly (handled by Docker CMD usually)
    # socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
    pass # Execution logic handled by Docker CMD
