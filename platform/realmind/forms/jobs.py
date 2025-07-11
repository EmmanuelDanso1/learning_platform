# forms/jobs.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed

class JobPostForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired(), Length(min=5, max=100)])
    description = TextAreaField('Job Description', validators=[DataRequired()])
    requirements = TextAreaField('Job Requirements', validators=[DataRequired()])
    submit = SubmitField('Post Job')

class ApplyJobForm(FlaskForm):
    cv = FileField('Upload CV', validators=[FileAllowed(['pdf', 'doc', 'docx']), DataRequired()])
    certificate = FileField('Upload Certificate', validators=[FileAllowed(['pdf', 'jpg', 'jpeg', 'png'])])
    submit = SubmitField('Apply')