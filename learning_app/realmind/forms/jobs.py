# forms/jobs.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed
class JobPostForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired(), Length(min=5, max=100)])
    description = TextAreaField('Job Description', validators=[DataRequired()])
    requirements = TextAreaField('Job Requirements', validators=[DataRequired()])
    level = SelectField('Level', validators=[DataRequired()], choices=[
        ('Pre-School', 'Pre-School'),
        ('Lower Primary', 'Lower Primary'),
        ('Upper Primary', 'Upper Primary'),
        ('Junior High', 'Junior High'),
        ('Lower Secondary', 'Lower Secondary'),
        ('Senior High', 'Senior High'),
        ('Upper Secondary', 'Upper Secondary'),
        ('O-Level', 'O-Level'),
        ('A-Level', 'A-Level')
    ])
    
    subject = SelectField('Subject', validators=[DataRequired()], choices=[
        ('Mathematics', 'Mathematics'),
        ('English', 'English'),
        ('Integrated Science', 'Integrated Science'),
        ('Creative Arts', 'Creative Arts'),
        ('Our World and Our People', 'Our World and Our People'),
        ('Ghanaian Language', 'Ghanaian Language'),
        ('Computing', 'Computing'),
        ('Physical Education', 'Physical Education'),
        ('Religious and Moral Education', 'Religious and Moral Education'),
        ('Elective Mathematics', 'Elective Mathematics'),
        ('Biology', 'Biology'),
        ('Physics', 'Physics'),
        ('Chemistry', 'Chemistry'),
        ('General Agriculture', 'General Agriculture'),
        ('Animal Husbandry', 'Animal Husbandry'),
        ('Crop Husbandry', 'Crop Husbandry'),
        ('Fisheries', 'Fisheries'),
        ('Forestry', 'Forestry'),
        ('Food and Nutrition', 'Food and Nutrition'),
        ('Management in Living', 'Management in Living'),
        ('Textile Studies', 'Textile Studies'),
        ('Visual Arts', 'Visual Arts'),
        ('Graphic Design', 'Graphic Design'),
        ('Sculpture', 'Sculpture'),
        ('Ceramics', 'Ceramics'),
        ('Picture Making', 'Picture Making'),
        ('General Knowledge in Art', 'General Knowledge in Art'),
        ('Music', 'Music'),
        ('French', 'French'),
        ('Literature in English', 'Literature in English'),
        ('Government', 'Government'),
        ('History', 'History'),
        ('Geography', 'Geography'),
        ('Economics', 'Economics'),
        ('Business Management', 'Business Management'),
        ('Financial Accounting', 'Financial Accounting'),
        ('Cost Accounting', 'Cost Accounting'),
        ('Elective ICT', 'Elective ICT'),
        ('Christian Religious Studies', 'Christian Religious Studies'),
        ('Islamic Religious Studies', 'Islamic Religious Studies'),
        ('Arabic', 'Arabic'),
        ('Tourism', 'Tourism'),
        ('Auto Mechanics', 'Auto Mechanics'),
        ('Welding and Fabrication', 'Welding and Fabrication'),
        ('Building Construction', 'Building Construction'),
        ('Technical Drawing', 'Technical Drawing'),
        ('Electrical Engineering Technology', 'Electrical Engineering Technology'),
        ('Plumbing', 'Plumbing'),
        ('Applied Electricity', 'Applied Electricity'),
        ('Electronics', 'Electronics'),
        ('Woodwork', 'Woodwork'),
        ('Metalwork', 'Metalwork'),
        ('Printing Craft', 'Printing Craft'),
        ('Spanish', 'Spanish'),
        ('Sewing', 'Sewing'),
        ('Pottery', 'Pottery'),
        ('Other', 'Other')
    ])
    submit = SubmitField('Post Job')

class ApplyJobForm(FlaskForm):
    cv = FileField('Upload CV', validators=[FileAllowed(['pdf', 'doc', 'docx']), DataRequired()])
    certificate = FileField('Upload Certificate', validators=[FileAllowed(['pdf', 'jpg', 'jpeg', 'png'])])
    submit = SubmitField('Apply')