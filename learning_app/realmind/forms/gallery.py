from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, DecimalField
from wtforms.validators import DataRequired, Length, EqualTo, Optional
from flask_wtf.file import FileRequired, FileAllowed

class GalleryUploadForm(FlaskForm):
    caption = StringField('Caption', validators=[DataRequired()])
    file = FileField('Upload File', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'mp4'], 'Images or videos only!')
    ])
    submit = SubmitField('Upload')
