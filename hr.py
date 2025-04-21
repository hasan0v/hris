from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
# Import db and models needed
from app import db
from models import User, Vacancy, UserRole, Application, ApplicationStatus # Added Application, ApplicationStatus
# Import forms
from forms import VacancyForm # Import the new form
# Import the actual decorator
from decorators import hr_required # Import the decorator

hr_bp = Blueprint('hr', __name__, url_prefix='/hr')

# Removed placeholder decorator

@hr_bp.route('/dashboard')
@login_required
@hr_required # Apply the decorator
def dashboard():
    # Role check is now handled by the decorator
    # if current_user.role != UserRole.HR:
    #      flash('Access denied.', 'danger')
    #      return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    per_page = 10 # Example pagination
    user_vacancies = Vacancy.query.filter_by(hr_id=current_user.id)\
                                  .order_by(Vacancy.created_at.desc())\
                                  .paginate(page=page, per_page=per_page, error_out=False)

    return render_template('hr/dashboard.html', title='HR Dashboard', vacancies=user_vacancies)

@hr_bp.route('/vacancy/new', methods=['GET', 'POST'])
@login_required
@hr_required # Apply the decorator
def create_vacancy():
    # Role check is now handled by the decorator
    # if current_user.role != UserRole.HR:
    #      flash('Access denied.', 'danger')
    #      return redirect(url_for('index'))

    form = VacancyForm()
    if form.validate_on_submit():
        # Create detailed weight dictionary from form data
        weights = {
            "relevant_experience_years": form.weight_relevant_experience_years.data,
            "technical_skills_match": form.weight_technical_skills_match.data,
            "education_level_relevance": form.weight_education_level_relevance.data,
            "project_portfolio_quality": form.weight_project_portfolio_quality.data,
            "keyword_alignment": form.weight_keyword_alignment.data,
            "communication_clarity": form.weight_communication_clarity.data
        }
        # Validation for sum=1.0 is now handled in the form's validate method
        # total_weight = sum(weights.values())
        # if not abs(total_weight - 1.0) < 0.001:
        #     flash('Weights must sum to 1.0.', 'danger')
        #     return render_template('hr/create_vacancy.html', title='Create New Vacancy', form=form)

        vacancy = Vacancy(title=form.title.data,
                          description=form.description.data,
                          hr_id=current_user.id,
                          weight_coefficients=weights) # Store weights as JSON
        db.session.add(vacancy)
        try:
            db.session.commit()
            flash('Vacancy created successfully!', 'success')
            return redirect(url_for('hr.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating vacancy: {e}', 'danger')

    # Render template
    return render_template('hr/create_vacancy.html', title='Create New Vacancy', form=form)

@hr_bp.route('/vacancy/<int:vacancy_id>/applicants')
@login_required
@hr_required # Apply the decorator
def view_applicants(vacancy_id):
    # Role check is now handled by the decorator
    # if current_user.role != UserRole.HR:
    #      flash('Access denied.', 'danger')
    #      return redirect(url_for('index'))

    vacancy = db.session.get(Vacancy, vacancy_id)
    if not vacancy or vacancy.hr_id != current_user.id:
        flash('Vacancy not found or you do not have permission to view it.', 'danger')
        return redirect(url_for('hr.dashboard'))

    # Fetch applications for this vacancy, ordered by score (descending, NULLs last - MySQL compatible)
    page = request.args.get('page', 1, type=int)
    per_page = 15 # Or another suitable number
    applications = Application.query.filter_by(vacancy_id=vacancy_id)\
                                    .order_by(Application.score.is_(None).asc(), Application.score.desc(), Application.application_date.asc())\
                                    .paginate(page=page, per_page=per_page, error_out=False) # Order by IS NULL first, then score DESC

    return render_template('hr/view_applicants.html',
                           title=f'Applicants for "{vacancy.title}"',
                           vacancy=vacancy,
                           applications=applications)

# Added imports for CSV export
import io
import csv
from flask import Response

@hr_bp.route('/vacancy/<int:vacancy_id>/applicants/export')
@login_required
@hr_required
def export_applicants(vacancy_id):
    vacancy = db.session.get(Vacancy, vacancy_id)
    if not vacancy or vacancy.hr_id != current_user.id:
        flash('Vacancy not found or you do not have permission to export.', 'danger')
        return redirect(url_for('hr.dashboard'))

    # Fetch ALL applications for this vacancy for export, ordered by score (MySQL compatible)
    applications = Application.query.filter_by(vacancy_id=vacancy_id)\
                                    .order_by(Application.score.is_(None).asc(), Application.score.desc(), Application.application_date.asc())\
                                    .all() # Order by IS NULL first, then score DESC

    # Use StringIO to write CSV data in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Define detailed header row based on new scoring sections
    header = [
        'Applicant Email', 'CV Filename', 'Applied Date', 'Status', 'Overall Score',
        'Relevant Experience Years Score', 'Technical Skills Match Score', 'Education Relevance Score',
        'Project/Portfolio Quality Score', 'Keyword Alignment Score', 'Communication Clarity Score'
    ]
    writer.writerow(header)

    # Write data rows
    for app in applications:
        # Safely get detailed scores, defaulting to empty string if breakdown or key is missing
        breakdown = app.score_breakdown or {}
        exp_score = breakdown.get('relevant_experience_years', '')
        tech_score = breakdown.get('technical_skills_match', '')
        edu_score = breakdown.get('education_level_relevance', '')
        proj_score = breakdown.get('project_portfolio_quality', '')
        key_score = breakdown.get('keyword_alignment', '')
        comm_score = breakdown.get('communication_clarity', '')

        writer.writerow([
            app.applicant.email,
            app.cv_file.filename,
            app.application_date.strftime('%Y-%m-%d %H:%M:%S'),
            app.status.value,
            f"{app.score:.2f}" if app.score is not None else '',
            f"{exp_score:.1f}" if isinstance(exp_score, (int, float)) else exp_score,
            f"{tech_score:.1f}" if isinstance(tech_score, (int, float)) else tech_score,
            f"{edu_score:.1f}" if isinstance(edu_score, (int, float)) else edu_score,
            f"{proj_score:.1f}" if isinstance(proj_score, (int, float)) else proj_score,
            f"{key_score:.1f}" if isinstance(key_score, (int, float)) else key_score,
            f"{comm_score:.1f}" if isinstance(comm_score, (int, float)) else comm_score
        ])

    output.seek(0) # Rewind the buffer

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=applicants_{vacancy.title.replace(' ','_')}_{vacancy_id}.csv"}
    )

@hr_bp.route('/application/shortlist/<int:app_id>', methods=['POST'])
@login_required
@hr_required
def shortlist_application(app_id):
    application = db.session.get(Application, app_id)
    if not application:
        flash('Application not found.', 'danger')
        return redirect(request.referrer or url_for('hr.dashboard')) # Redirect back

    # Check if HR user owns the vacancy associated with the application
    vacancy = db.session.get(Vacancy, application.vacancy_id) # Need Vacancy model
    if not vacancy or vacancy.hr_id != current_user.id:
        flash('Permission denied to modify this application.', 'danger')
        return redirect(request.referrer or url_for('hr.dashboard'))

    # Update status
    application.status = ApplicationStatus.SHORTLISTED # Need ApplicationStatus enum
    db.session.add(application)
    try:
        db.session.commit()
        flash(f'Application for {application.applicant.email} shortlisted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error shortlisting application: {e}', 'danger')

    return redirect(request.referrer or url_for('hr.view_applicants', vacancy_id=application.vacancy_id))


@hr_bp.route('/application/reject/<int:app_id>', methods=['POST'])
@login_required
@hr_required
def reject_application(app_id):
    application = db.session.get(Application, app_id)
    if not application:
        flash('Application not found.', 'danger')
        return redirect(request.referrer or url_for('hr.dashboard')) # Redirect back

    # Check if HR user owns the vacancy associated with the application
    vacancy = db.session.get(Vacancy, application.vacancy_id) # Need Vacancy model
    if not vacancy or vacancy.hr_id != current_user.id:
        flash('Permission denied to modify this application.', 'danger')
        return redirect(request.referrer or url_for('hr.dashboard'))

    # Update status
    application.status = ApplicationStatus.REJECTED # Need ApplicationStatus enum
    db.session.add(application)
    try:
        db.session.commit()
        flash(f'Application for {application.applicant.email} rejected.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting application: {e}', 'danger')

    return redirect(request.referrer or url_for('hr.view_applicants', vacancy_id=application.vacancy_id))

@hr_bp.route('/vacancy/delete/<int:vacancy_id>', methods=['POST'])
@login_required
@hr_required
def delete_vacancy(vacancy_id):
    vacancy = db.session.get(Vacancy, vacancy_id)
    if not vacancy or vacancy.hr_id != current_user.id:
        flash('Vacancy not found or permission denied.', 'danger')
        return redirect(url_for('hr.dashboard'))

    try:
        # Delete associated applications first (handle potential constraints)
        Application.query.filter_by(vacancy_id=vacancy_id).delete()
        # Delete the vacancy itself
        db.session.delete(vacancy)
        db.session.commit()
        flash(f'Vacancy "{vacancy.title}" and all associated applications deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting vacancy: {e}', 'danger')
        current_app.logger.error(f"Vacancy deletion failed for vacancy {vacancy_id}, user {current_user.id}: {e}", exc_info=True)

    return redirect(url_for('hr.dashboard'))


# Add routes for editing vacancies later
