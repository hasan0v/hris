from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
# Import User model to check for existing email
from models import User, UserRole
# Import lazy_gettext for form labels - Removed
# from flask_babel import lazy_gettext as _l

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)]) # Added
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)]) # Added
    company_name = StringField('Company Name (Optional - for HR)', validators=[Length(max=128)]) # Added
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password', message='Passwords must match.')]) # Reverted message
    # Simple role selection for MVP
    role = SelectField('Register as', choices=[(UserRole.APPLICANT.value, 'Applicant'), (UserRole.HR.value, 'HR Recruiter')], # Reverted choices
                       validators=[DataRequired()])
    submit = SubmitField('Register')

    # Custom validator to check if email already exists
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            # Reverted validation error message
            raise ValidationError('That email is already registered. Please choose a different one or login.')

# Added import for TextAreaField, FloatField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, FileField, FloatField
from wtforms.validators import NumberRange # Added NumberRange validator

class VacancyForm(FlaskForm):
    title = StringField('Vacancy Title', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description')
    # Detailed weight coefficients fields
    weight_relevant_experience_years = FloatField('Relevant Experience (Years) Weight', default=0.25, validators=[DataRequired(), NumberRange(min=0.0, max=1.0)])
    weight_technical_skills_match = FloatField('Technical Skills Match Weight', default=0.30, validators=[DataRequired(), NumberRange(min=0.0, max=1.0)])
    weight_education_level_relevance = FloatField('Education Relevance Weight', default=0.15, validators=[DataRequired(), NumberRange(min=0.0, max=1.0)])
    weight_project_portfolio_quality = FloatField('Project/Portfolio Quality Weight', default=0.10, validators=[DataRequired(), NumberRange(min=0.0, max=1.0)])
    weight_keyword_alignment = FloatField('Keyword Alignment Weight', default=0.10, validators=[DataRequired(), NumberRange(min=0.0, max=1.0)])
    weight_communication_clarity = FloatField('Communication Clarity Weight', default=0.10, validators=[DataRequired(), NumberRange(min=0.0, max=1.0)])
    submit = SubmitField('Create Vacancy')

    # Validator to check if detailed weights sum to 1.0
    # def validate(self, extra_validators=None):
    #     if not super().validate(extra_validators):
    #         return False
    #     total_weight = (self.weight_experience.data or 0) + \
    #                    (self.weight_education.data or 0) + \
    #                    (self.weight_skills.data or 0)
    def validate(self, extra_validators=None):
        # Run default validators first
        initial_validation = super(VacancyForm, self).validate(extra_validators)
        if not initial_validation:
            return False

        # Check if weights sum to 1.0 (within a small tolerance)
        total_weight = sum([
            self.weight_relevant_experience_years.data or 0,
            self.weight_technical_skills_match.data or 0,
            self.weight_education_level_relevance.data or 0,
            self.weight_project_portfolio_quality.data or 0,
            self.weight_keyword_alignment.data or 0,
            self.weight_communication_clarity.data or 0
        ])

        if not abs(total_weight - 1.0) < 0.001: # Check for floating point precision
            # Add error to a specific field or a general form error
            self.weight_relevant_experience_years.errors.append('Weights for all sections must sum exactly to 1.0')
            return False
        return True

# Added import for FileField and FileAllowed/FileRequired validators
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, FileField
from flask_wtf.file import FileAllowed, FileRequired

class CVUploadForm(FlaskForm):
    cv_file = FileField('Upload CV (PDF or DOCX)', validators=[
        FileRequired(message='Please select a file.'), # Reverted message
        FileAllowed(['pdf', 'docx'], 'Only PDF and DOCX files are allowed!') # Reverted message
    ])
    submit = SubmitField('Upload CV')
