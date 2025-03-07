from flask import Flask
from os import path
from flask_mail import Mail
import locale
from datetime import datetime
from .models import db
from .models import Classroom, Profesor
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

mail = Mail()
DB_NAME = 'database1.db'
locale.setlocale(locale.LC_TIME, 'hr_HR.UTF-8')

def create_app():
    global limiter
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'diwadhuawidhaa'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = 'zamjenehr@gmail.com'
    app.config['MAIL_PASSWORD'] = 'npqr xggb wcss qzsc' #zamjenehrlozinka
    app.config['MAIL_DEFAULT_SENDER'] = 'zamjenehr@gmail.com'

    mail.init_app(app)
    db.init_app(app)

    limiter = Limiter(get_remote_address, app=app, default_limits=["10000 per day", "100 per minute"])

    from .views import views
    app.register_blueprint(views, url_prefix='/')

    create_db(app)

    @app.template_filter('split')
    def split_filter(value, delimiter='|'):
        return value.split(delimiter)

    @app.template_filter('dan')
    def dan_filter(value):
        date = datetime.strptime(value, '%Y-%m-%d')
        day_of_week = date.weekday()
        day_names = {0: 'Ponedjeljak', 1: 'Utorak', 2: 'Srijeda', 3: 'Četvrtak', 4: 'Petak', 5: 'Subota', 6: 'Nedjelja'}
        return day_names[day_of_week]

    @app.template_filter('razred')
    def razred_filter(value):
        try:
            classroom = Classroom.query.get(value).name
            return classroom
        except:
            return "Nepoznato"

    @app.template_filter('profesor')
    def profesor_filter(value):
        try:
            profesor = Profesor.query.get(value).name
            return profesor
        except:
            return "Nepoznato"

    return app

def create_db(app):
    if not path.exists('instance/' + DB_NAME):
        with app.app_context():
            db.create_all()
