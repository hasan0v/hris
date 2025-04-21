import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
# Import db, models, AND socketio instance
from app import db, socketio # Import socketio instance
from models import User, Application, CVFile, UserRole, ApplicationStatus, Vacancy # Added Vacancy
# Import forms
from forms import CVUploadForm # Import the new form
# Import utilities for parsing and scoring
from utils import parse_cv, get_openai_score
# Import the actual decorator
from decorators import applicant_required # Import the decorator

applicant_bp = Blueprint('applicant', __name__, url_prefix='/applicant')

# Removed placeholder decorator

@applicant_bp.route('/dashboard')
@login_required
@applicant_required # Apply the decorator
def dashboard():
    # Role check is now handled by the decorator
    # if current_user.role != UserRole.APPLICANT:
    #      flash('Access denied.', 'danger')
    #      return redirect(url_for('index'))

    # Fetch user's applications and CVs (add pagination later if needed)
    user_applications = Application.query.filter_by(applicant_id=current_user.id)\
                                         .order_by(Application.application_date.desc()).all()
    user_cvs = CVFile.query.filter_by(applicant_id=current_user.id)\
                            .order_by(CVFile.upload_date.desc()).all()

    # CV Upload form
    upload_form = CVUploadForm() # Instantiate the form

    return render_template('applicant/dashboard.html',
                           title='Applicant Dashboard',
                           applications=user_applications,
                           cvs=user_cvs,
                           upload_form=upload_form) # Pass form to template (Corrected position)


@applicant_bp.route('/cv/upload', methods=['POST']) # POST only for file upload
@login_required
@applicant_required # Apply the decorator
def upload_cv():
     # Role check is now handled by the decorator
    # if current_user.role != UserRole.APPLICANT:
    #      flash('Access denied.', 'danger')
    #      return redirect(url_for('index'))

    form = CVUploadForm() # Instantiate the form
    if form.validate_on_submit():
        # Check CV limit (FR-02: max 5 CVs)
        current_cv_count = CVFile.query.filter_by(applicant_id=current_user.id).count()
        if current_cv_count >= 5:
            flash('You have reached the maximum limit of 5 stored CVs.', 'warning')
            return redirect(url_for('applicant.dashboard')) # Return early if limit reached

        # --- File processing logic ---
        file = form.cv_file.data
        original_filename = secure_filename(file.filename)
        file_ext = os.path.splitext(original_filename)[1].lower()

        # Extension validation is handled by FileAllowed validator in the form
        # Size validation is handled by MAX_CONTENT_LENGTH in Flask config

        # Construct filepath (ensure upload path exists)
        upload_path = current_app.config['UPLOAD_PATH']
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)

        # Create a unique filename using UUID to prevent collisions
        unique_filename = f"{current_user.id}_{uuid.uuid4().hex}{file_ext}"
        filepath = os.path.join(upload_path, unique_filename)

        try:
            file.save(filepath)
            # Get file size after saving
            file_size = os.path.getsize(filepath)

            # Check against MAX_CONTENT_LENGTH again just in case (though Flask should handle)
            if file_size > current_app.config['MAX_CONTENT_LENGTH']:
                 os.remove(filepath) # Clean up oversized file
                 flash(f'File exceeds maximum size limit ({current_app.config["MAX_CONTENT_LENGTH"] / 1024 / 1024} MB).', 'danger')
                 return redirect(url_for('applicant.dashboard'))


            # Create CVFile record
            cv_record = CVFile(applicant_id=current_user.id,
                               filename=original_filename, # Store original filename for display
                               filepath=filepath, # Store path to saved file
                               file_size=file_size)
            db.session.add(cv_record)
            db.session.commit()
            flash('CV uploaded successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            # Attempt to clean up saved file if DB commit fails
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass # Ignore cleanup error
            flash(f'Error uploading CV: {e}', 'danger')
        # --- End of file processing logic ---

    else:
        # Handle form validation errors (e.g., wrong file type)
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')

    # Redirect back to dashboard after processing (success or failure)
    return redirect(url_for('applicant.dashboard'))

@applicant_bp.route('/application/withdraw/<int:app_id>', methods=['POST'])
@login_required
@applicant_required
def withdraw_application(app_id):
    application = db.session.get(Application, app_id)

    if not application or application.applicant_id != current_user.id:
        flash('Application not found or permission denied.', 'danger')
        return redirect(url_for('applicant.dashboard'))

    # Check if application can be withdrawn
    if application.status in [ApplicationStatus.WITHDRAWN, ApplicationStatus.REJECTED, ApplicationStatus.SHORTLISTED]:
        flash(f'Application status ({application.status.value}) does not allow withdrawal.', 'warning')
        return redirect(url_for('applicant.dashboard'))

    # Update status
    application.status = ApplicationStatus.WITHDRAWN
    db.session.add(application)
    try:
        db.session.commit()
        flash('Application withdrawn successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error withdrawing application: {e}', 'danger')
        current_app.logger.error(f"Application withdrawal failed for app {app_id}, user {current_user.id}: {e}", exc_info=True)

    # Ensure redirect happens outside the try/except block and at the correct indentation
    return redirect(url_for('applicant.dashboard'))

# --- Removed trigger_score route ---

@applicant_bp.route('/apply/<int:vacancy_id>', methods=['POST']) # Use POST to create a resource (application)
@login_required
@applicant_required # Apply the decorator
def apply_for_vacancy(vacancy_id):
    # Role check is now handled by the decorator
    # if current_user.role != UserRole.APPLICANT:
    #      flash('Only applicants can apply for vacancies.', 'danger')
    #      return redirect(url_for('index')) # Redirect to index or login

    # Find the vacancy
    vacancy = db.session.get(Vacancy, vacancy_id)
    if not vacancy:
        flash('Vacancy not found.', 'danger')
        return redirect(url_for('index'))

    # Check if already applied
    existing_application = Application.query.filter_by(
        applicant_id=current_user.id,
        vacancy_id=vacancy_id
    ).first()
    if existing_application:
        flash('You have already applied for this vacancy.', 'warning')
        return redirect(url_for('index')) # Or applicant dashboard

    # Find the applicant's most recent CV
    latest_cv = CVFile.query.filter_by(applicant_id=current_user.id)\
                            .order_by(CVFile.upload_date.desc())\
                            .first()
    if not latest_cv:
        flash('You must upload a CV before applying.', 'warning')
        # Redirect to dashboard where they can upload
        return redirect(url_for('applicant.dashboard'))

    # Create the application record
    new_application = Application(
        applicant_id=current_user.id,
        vacancy_id=vacancy_id,
        cv_file_id=latest_cv.id,
        status=ApplicationStatus.SUBMITTED # Initial status
    )
    db.session.add(new_application)

    try:
        db.session.commit() # Commit the initial application record
        flash(f'Successfully applied for "{vacancy.title}" using CV "{latest_cv.filename}". Scoring initiated...', 'success')

        # --- Start Scoring Process Inline ---
        new_application.status = ApplicationStatus.SCORING
        db.session.add(new_application)
        db.session.commit() # Commit status change

        try:
            # 1. Parse CV
            cv_text = parse_cv(latest_cv.filepath)
            if not cv_text:
                raise ValueError("Failed to parse CV text.")

            # 2. Get OpenAI Score
            score_breakdown = get_openai_score(cv_text, vacancy.description)
            if not score_breakdown:
                 raise ValueError("Failed to get score from OpenAI.")

            # 3. Calculate Weighted Score
            weights = vacancy.weight_coefficients
            if not weights:
                raise ValueError(f"Weight coefficients not set for vacancy ID {vacancy.id}")

            total_score = 0.0
            for section, weight in weights.items():
                section_score = score_breakdown.get(section)
                if section_score is not None:
                    try:
                        total_score += float(section_score) * float(weight)
                    except (TypeError, ValueError):
                         current_app.logger.warning(f"Could not convert score/weight for section '{section}' in application {new_application.id}.")
                         pass
                else:
                     current_app.logger.warning(f"Score section '{section}' not found in OpenAI response for application {new_application.id}.")

            final_score = round(total_score, 2)

            # 4. Update Application Record with Scores
            new_application.score_breakdown = score_breakdown
            new_application.score = final_score
            new_application.status = ApplicationStatus.SCORED
            db.session.add(new_application)
            db.session.commit()
            flash(f'Scoring complete for {vacancy.title}!', 'info') # Additional flash

            # Emit Socket.IO event
            try:
                user_room = f'user_{current_user.id}'
                socketio.emit('score_update', {
                    'application_id': new_application.id,
                    'vacancy_title': vacancy.title,
                    'status': new_application.status.value,
                    'score': new_application.score,
                    'score_breakdown': new_application.score_breakdown
                }, room=user_room)
                current_app.logger.info(f"Emitted score_update event to room {user_room}")
            except Exception as socket_e:
                current_app.logger.error(f"Failed to emit score_update event: {socket_e}", exc_info=True)

        except Exception as scoring_e:
            # Scoring failed, rollback score/status updates, keep application as SUBMITTED
            db.session.rollback()
            app_to_reset = db.session.get(Application, new_application.id)
            if app_to_reset:
                 app_to_reset.status = ApplicationStatus.SUBMITTED # Revert status
                 db.session.add(app_to_reset)
                 db.session.commit()
            flash(f'Error during scoring process: {scoring_e}', 'danger')
            current_app.logger.error(f"Scoring failed for application {new_application.id}: {scoring_e}", exc_info=True)
            # Still redirect to dashboard even if scoring fails, app exists as SUBMITTED
            return redirect(url_for('applicant.dashboard'))

        # Redirect to dashboard after successful application and scoring
        return redirect(url_for('applicant.dashboard'))

    except Exception as e:
        # Error during initial application commit
        db.session.rollback()
        flash(f'Error submitting application: {e}', 'danger')
        current_app.logger.error(f"Application submission failed for user {current_user.id}, vacancy {vacancy_id}: {e}", exc_info=True)
        return redirect(url_for('index')) # Redirect back to index on error

@applicant_bp.route('/cv/delete/<int:cv_id>', methods=['POST'])
@login_required
@applicant_required
def delete_cv(cv_id):
    cv_file = db.session.get(CVFile, cv_id)

    if not cv_file or cv_file.applicant_id != current_user.id:
        flash('CV not found or permission denied.', 'danger')
        return redirect(url_for('applicant.dashboard'))

    # Optional: Check if CV is linked to any non-final state applications
    active_apps = Application.query.filter_by(cv_file_id=cv_id).filter(
        Application.status.notin_([ApplicationStatus.WITHDRAWN, ApplicationStatus.REJECTED])
    ).count()

    if active_apps > 0:
        flash('Cannot delete CV as it is linked to active or pending applications.', 'warning')
        return redirect(url_for('applicant.dashboard'))

    # Proceed with deletion
    filepath = cv_file.filepath
    try:
        db.session.delete(cv_file)
        # Try to delete the physical file
        if os.path.exists(filepath):
            os.remove(filepath)
        db.session.commit()
        flash(f'CV "{cv_file.filename}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting CV: {e}', 'danger')
        current_app.logger.error(f"CV deletion failed for cv {cv_id}, user {current_user.id}: {e}", exc_info=True)

    return redirect(url_for('applicant.dashboard'))
