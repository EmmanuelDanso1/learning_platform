from flask import Blueprint, render_template, request
from learning_app.realmind.models import JobPost

job_bp = Blueprint('jobs', __name__)

@job_bp.route("/job")
def job():
    jobs = JobPost.query.order_by(JobPost.id.desc()).all()
    return render_template("jobs.html", title="Job", jobs=jobs)


@job_bp.route('/jobs')
def job_listings():
    keyword = request.args.get('keyword', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 5

    query = JobPost.query
    if keyword:
        query = query.filter(JobPost.title.ilike(f"%{keyword}%"))

    jobs = query.order_by(JobPost.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template('jobs.html',
                           jobs=jobs.items,
                           current_page=page,
                           total_pages=jobs.pages,
                           keyword=keyword)
