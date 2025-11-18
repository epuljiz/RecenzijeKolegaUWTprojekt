from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, RadioField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange
from flask_wtf.file import FileField, FileAllowed


class ReviewForm(FlaskForm):
    reviewed_user_email = StringField(
        'Email kolege', validators=[DataRequired(), Email()])
    rating = RadioField('Ocjena',
                        choices=[
                            (1, '1 ⭐'),
                            (2, '2 ⭐⭐'),
                            (3, '3 ⭐⭐⭐'),
                            (4, '4 ⭐⭐⭐⭐'),
                            (5, '5 ⭐⭐⭐⭐⭐')
                        ],
                        validators=[DataRequired()],
                        coerce=int)
    project_type = SelectField('Vrsta projekta/suradnje', choices=[
        ('', 'Odaberi vrstu suradnje'),
        ('Fakultetski projekt', 'Fakultetski projekt'),
        ('Timski rad', 'Timski rad'),
        ('Zadaća', 'Zadaća'),
        ('Laboratorijska vježba', 'Laboratorijska vježba'),
        ('Istraživački rad', 'Istraživački rad'),
        ('Drugo', 'Drugo')
    ])
    comment = TextAreaField('Komentar',
                            validators=[DataRequired(), Length(
                                min=10, max=1000)],
                            render_kw={"rows": 5, "placeholder": "Opiši svoje iskustvo suradnje..."})
    submit = SubmitField('Objavi recenziju')


class EditReviewForm(FlaskForm):
    rating = RadioField('Ocjena',
                        choices=[
                            (1, '1 ⭐'),
                            (2, '2 ⭐⭐'),
                            (3, '3 ⭐⭐⭐'),
                            (4, '4 ⭐⭐⭐⭐'),
                            (5, '5 ⭐⭐⭐⭐⭐')
                        ],
                        validators=[DataRequired()],
                        coerce=int)
    project_type = SelectField('Vrsta projekta/suradnje', choices=[
        ('', 'Odaberi vrstu suradnje'),
        ('Fakultetski projekt', 'Fakultetski projekt'),
        ('Timski rad', 'Timski rad'),
        ('Zadaća', 'Zadaća'),
        ('Laboratorijska vježba', 'Laboratorijska vježba'),
        ('Istraživački rad', 'Istraživački rad'),
        ('Drugo', 'Drugo')
    ])
    comment = TextAreaField('Komentar',
                            validators=[DataRequired(), Length(
                                min=10, max=1000)],
                            render_kw={"rows": 5})
    submit = SubmitField('Ažuriraj recenziju')
