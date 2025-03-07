from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)

    school = db.relationship('School', backref=db.backref('users', lazy=True))
    classroom = db.relationship('Classroom', backref=db.backref('users', lazy=True))

    date_added = db.Column(db.DateTime, default=datetime.utcnow)


class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    login_password = db.Column(db.String(100), nullable=False)

    date_added = db.Column(db.DateTime, default=datetime.utcnow)


class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    razrednik = db.Column(db.String(100), nullable=False)
    school = db.relationship('School', backref=db.backref('classrooms', lazy=True))

    date_added = db.Column(db.DateTime, default=datetime.utcnow)


class Zamjene(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    od = db.Column(db.String(100), nullable=False)
    do = db.Column(db.String(100), nullable=False)
    datum = db.Column(db.Date, nullable=False)
    zamjena = db.Column(db.String(100), nullable=False)
    stariprofesor = db.Column(db.String(100), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    classroom_name = db.Column(db.String(100), nullable=True)
    biljeska = db.Column(db.String(100), nullable=True)
    dodao_profesor = db.Column(db.Integer)

    date_added = db.Column(db.DateTime, default=datetime.utcnow)


class RasporedSati(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    raspored_string = db.Column(db.String(1000), nullable=False)

    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class RasporedSatiPopodne(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    raspored_string = db.Column(db.String(1000), nullable=False)

    date_added = db.Column(db.DateTime, default=datetime.utcnow)



class RasporedUcionica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    raspored_string = db.Column(db.String(10000), nullable=False)

    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class RasporedUcionicaPopodne(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    raspored_string = db.Column(db.String(10000), nullable=False)

    date_added = db.Column(db.DateTime, default=datetime.utcnow)


class Obavjesti(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(100), nullable=False)
    dodao_profesor = db.Column(db.Integer)

    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class Predmeti(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    predmet = db.Column(db.String(100), nullable=False)
    profesor = db.Column(db.String(100), nullable=False)

    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class Profesor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    pin = db.Column(db.Integer)
    is_admin = db.Column(db.Integer, default=0)
    email = db.Column(db.String(100), nullable=False, default="noemail")

    date_added = db.Column(db.DateTime, default=datetime.utcnow)

