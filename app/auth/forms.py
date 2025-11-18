from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class RegistrationForm(FlaskForm):
    name = StringField('Ime i prezime', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email adresa', validators=[DataRequired(), Email()])
    password = PasswordField('Lozinka', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Potvrdi lozinku', 
                                   validators=[DataRequired(), EqualTo('password')])
    faculty = SelectField('Fakultet', choices=[
        ('', 'Odaberi fakultet'),
        ('Elektrotehnika i računarstvo', 'Elektrotehnika i računarstvo'),
        ('Arhitektura', 'Arhitektura'),
        ('Gradjevinski fakultet', 'Građevinski fakultet'),
        ('Medicina', 'Medicina'),
        ('Pravo', 'Pravo'),
        ('Ekonomija', 'Ekonomija'),
        ('Filozofski fakultet', 'Filozofski fakultet'),
        ('Kinezologija', 'Kinezologija'),
        ('Drugi', 'Drugi')
    ])
    department = StringField('Odjel/Smjer')
    submit = SubmitField('Registriraj se')

class LoginForm(FlaskForm):
    email = StringField('Email adresa', validators=[DataRequired(), Email()])
    password = PasswordField('Lozinka', validators=[DataRequired()])
    submit = SubmitField('Prijavi se')