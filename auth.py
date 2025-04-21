from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
# from flask_babel import gettext as _ # Removed gettext import
# Import db and models needed
from app import db
from models import User, UserRole
# Import forms
from forms import LoginForm, RegistrationForm # Changed to absolute import

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index')) # Or redirect to user's dashboard

    form = RegistrationForm()
    if form.validate_on_submit():
        # Determine role from form selection
        selected_role = UserRole(form.role.data) # Convert string value back to Enum
        user = User(
            email=form.email.data,
            role=selected_role,
            first_name=form.first_name.data, # Added
            last_name=form.last_name.data,   # Added
            company_name=form.company_name.data if form.company_name.data else None # Added (handle empty string)
        )
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
            flash('Registration successful! Please log in.', 'success') # Reverted
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error during registration: {e}', 'danger') # Reverted (using f-string)

    # Render template
    return render_template('auth/register.html', title='Register', form=form) # Reverted

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index')) # Or redirect to user's dashboard

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('Login successful!', 'success') # Reverted
            next_page = request.args.get('next')
            # Redirect logic based on role
            if user.role == UserRole.HR:
                # Redirect to HR dashboard (create later)
                # return redirect(next_page or url_for('hr.dashboard'))
                return redirect(next_page or url_for('index')) # Placeholder
            else:
                # Redirect to Applicant dashboard (create later)
                # return redirect(next_page or url_for('applicant.dashboard'))
                return redirect(next_page or url_for('index')) # Placeholder
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger') # Reverted

    # Render template
    return render_template('auth/login.html', title='Login', form=form) # Reverted


@auth_bp.route('/logout')
@login_required # User must be logged in to logout
def logout():
    logout_user()
    flash('You have been logged out.', 'info') # Reverted
    return redirect(url_for('index'))

# Add other auth routes if needed (e.g., password reset)
