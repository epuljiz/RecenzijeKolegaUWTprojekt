from itsdangerous import URLSafeTimedSerializer
from flask import current_app, url_for
from flask_mail import Message
from ..extensions import mail


def generate_verification_token():
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps('email_verification', salt='email-verify')


def verify_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        serializer.loads(token, salt='email-verify', max_age=expiration)
        return True
    except:
        return False


def send_verification_email(user):
    token = user.verification_token
    verify_url = url_for('auth.verify_email', token=token, _external=True)

    msg = Message(
        subject='Verificirajte svoj email - KolegaRecenzije',
        recipients=[user.email],
        sender=current_app.config['MAIL_USERNAME']
    )

    msg.body = f'''
Poštovani/a {user.name},

Hvala vam što ste se registrirali na KolegaRecenzije!
Molimo kliknite na sljedeći link kako biste verificirali svoju email adresu:

{verify_url}

Ovaj link će istjecí za 1 sat.

Ako niste zatražili ovaj email, molimo ignorirajte ga.

Lijep pozdrav,
Tim KolegaRecenzije
'''

    mail.send(msg)
