import enum
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db # Import db instance from app.py (Changed to absolute)

class UserRole(enum.Enum):
    APPLICANT = 'applicant'
    HR = 'hr'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256)) # Increased length for future hash algorithms
    first_name = db.Column(db.String(64), nullable=True) # Added
    last_name = db.Column(db.String(64), nullable=True) # Added
    company_name = db.Column(db.String(128), nullable=True) # Added (Optional, maybe more relevant for HR)
    role = db.Column(db.Enum(UserRole), default=UserRole.APPLICANT, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    applications = db.relationship('Application', backref='applicant', lazy='dynamic', foreign_keys='Application.applicant_id')
    vacancies_created = db.relationship('Vacancy', backref='hr_creator', lazy='dynamic', foreign_keys='Vacancy.hr_id')
    cv_files = db.relationship('CVFile', backref='owner', lazy='dynamic', foreign_keys='CVFile.applicant_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        # Property to easily get full name
        @property
        def full_name(self):
            if self.first_name and self.last_name:
                return f"{self.first_name} {self.last_name}"
            elif self.first_name:
                return self.first_name
            elif self.last_name:
                return self.last_name
            else:
                return self.email # Fallback to email

        return f'<User {self.id}: {self.email} ({self.role.value})>'

class Vacancy(db.Model):
    __tablename__ = 'vacancies'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    hr_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Link to HR user
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    # Store weights as JSON - flexible for adding/changing sections
    # Example: {"experience": 0.4, "education": 0.3, "skills": 0.3}
    weight_coefficients = db.Column(db.JSON, nullable=True) # Default weights applied if null

    # Relationships
    applications = db.relationship('Application', backref='vacancy', lazy='dynamic', foreign_keys='Application.vacancy_id')

    def __repr__(self):
        return f'<Vacancy {self.id}: {self.title}>'

class CVFile(db.Model):
    __tablename__ = 'cv_files'
    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Link to Applicant user
    filename = db.Column(db.String(255), nullable=False)
    # Store file path relative to UPLOAD_PATH defined in config
    # Consider storing blob directly for smaller scale or using dedicated storage service
    filepath = db.Column(db.String(512), nullable=False, unique=True)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    file_size = db.Column(db.Integer) # Size in bytes
    # Store parsed text temporarily? PRD says purge raw text after 24h.
    # parsed_text = db.Column(db.Text, nullable=True)
    # parsed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    applications = db.relationship('Application', backref='cv_file', lazy='dynamic', foreign_keys='Application.cv_file_id')

    def __repr__(self):
        return f'<CVFile {self.id}: {self.filename} for User {self.applicant_id}>'

class ApplicationStatus(enum.Enum):
    SUBMITTED = 'submitted'
    SCORING = 'scoring' # Intermediate state
    SCORED = 'scored'
    SHORTLISTED = 'shortlisted' # By HR
    REJECTED = 'rejected'     # By HR
    WITHDRAWN = 'withdrawn'   # By Applicant (FR-07)

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vacancy_id = db.Column(db.Integer, db.ForeignKey('vacancies.id'), nullable=False)
    cv_file_id = db.Column(db.Integer, db.ForeignKey('cv_files.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.Enum(ApplicationStatus), default=ApplicationStatus.SUBMITTED, nullable=False, index=True)
    # Store overall score (weighted)
    score = db.Column(db.Float(precision=2), nullable=True) # Precision 0.01 as per FR-05
    # Store detailed section scores from LLM (before weighting)
    score_breakdown = db.Column(db.JSON, nullable=True) # e.g., {"experience": 4.5, "education": 3.0, ...}
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Ensure one application per user per vacancy
    __table_args__ = (db.UniqueConstraint('applicant_id', 'vacancy_id', name='_applicant_vacancy_uc'),)

    def __repr__(self):
        return f'<Application {self.id} by User {self.applicant_id} for Vacancy {self.vacancy_id}>'

# Add LoginManager configuration later in app.py or extensions.py
# from flask_login import LoginManager
# login_manager = LoginManager()
# login_manager.login_view = 'auth.login' # Example blueprint route

# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))
