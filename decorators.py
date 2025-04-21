from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from models import UserRole # Import the UserRole enum

def role_required(required_role):
    """
    Decorator to ensure a user is logged in and has a specific role.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            if current_user.role != required_role:
                flash('You do not have permission to access this page.', 'danger')
                # Redirect to appropriate dashboard or index based on actual role?
                # For now, redirect to index.
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Specific decorators using the generic one
def hr_required(f):
    return role_required(UserRole.HR)(f)

def applicant_required(f):
    return role_required(UserRole.APPLICANT)(f)
