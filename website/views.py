from flask import Blueprint, render_template, Flask, request, redirect, make_response, url_for, jsonify, current_app, send_file
from .models import User, School, Classroom, Zamjene, Obavjesti, RasporedSati, RasporedUcionica, Predmeti, Profesor, RasporedSatiPopodne, RasporedUcionicaPopodne
from . import db, mail, limiter
import time
import pandas as pd
import os
from werkzeug.utils import secure_filename
from datetime import datetime, date, timedelta
import random
import string
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from sqlalchemy import func, cast, String, asc, desc
import locale
from cryptography.fernet import Fernet
import threading
import io

views = Blueprint('views', __name__)

locale.setlocale(locale.LC_TIME, 'hr_HR.UTF-8')

def send_email_in_context(app, user_email, subject, body):
    with app.app_context():
        try:
            message = Message(subject=subject,
                            recipients=[user_email],
                            body=body)
            mail.send(message)
        except Exception as e:
            app.logger.error(f"Failed to send email to {user_email}: {e}")
#key = Fernet.generate_key()
key = "ukg5f4ShyZgTCmIzWSRZjWL2dn2BtJ2nG1DWF55-cgE=".encode()
cipher_suite = Fernet(key)
def decrypt_cookie(cookie):
    try:
        decrypted_value = cipher_suite.decrypt(cookie.encode())
        return decrypted_value.decode()
    except:
        return None


#home page stranice
@views.route('/')
def home():
    userDevice = request.headers.get('User-Agent')
    isUserLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    isAdminLoggedIn = decrypt_cookie(request.cookies.get('isAdminLoggedIn'))
    isSkolaLoggedIn = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))

    sveObavijesti=[]
    zamjeneDanas=[]
    zamjeneSutra=[]
    zamjenePrekosutra=[]
    zamjeneSljedeciTjedan=[]

    if isSkolaLoggedIn=="True":
        loggedInSkolaID = int(decrypt_cookie(request.cookies.get('loggedInSchoolID')))
        loggedInProfID = int(decrypt_cookie(request.cookies.get('loggedInProfesorID')))
        profesor = Profesor.query.filter_by(id=loggedInProfID).first()
        loggedInProf = Profesor.query.filter_by(id=loggedInProfID).first()

        today = date.today()
        tomarrow = today + timedelta(days=1)
        dayAfterTomarrow = tomarrow + timedelta(days=1)

        professor_name = loggedInProf.name

        zamjeneDanas = Zamjene.query.filter(Zamjene.zamjena.like(f"%{professor_name}%"), Zamjene.datum==today).all()

        daysUntilNextMonday = (-1 - today.weekday()) % 7
        nextMonday = today + timedelta(days=daysUntilNextMonday + 1)
        nextWeekStart = nextMonday
        nextWeekEnd = nextMonday + timedelta(days=6)
        next3WeeksEnd = nextMonday + timedelta(days=20)

        zamjeneOvajTjedan = Zamjene.query.filter(Zamjene.zamjena.like(f"%{professor_name}%"), Zamjene.datum>=today, Zamjene.datum<nextWeekStart).all()

        zamjeneIducaTriTjedna = Zamjene.query.filter(Zamjene.datum >= nextWeekStart,Zamjene.datum <= next3WeeksEnd, Zamjene.zamjena.like(f"%{professor_name}%")).order_by(Zamjene.datum).all()

        zamjeneUmjestoUlogiranogProfesora = Zamjene.query.filter(Zamjene.datum >= today, Zamjene.datum <= nextWeekEnd, Zamjene.stariprofesor==professor_name).order_by(Zamjene.datum).all()

        sveObavijesti = Obavjesti.query.filter(Obavjesti.school_id == loggedInSkolaID,Obavjesti.date_added >= (datetime.utcnow() - timedelta(days=7))).order_by(Obavjesti.date_added.desc()).all()

        if 'Mobile' in userDevice:
            return render_template("templates-mobile/home_mobile.html", zamjeneIducaTriTjedna=zamjeneIducaTriTjedna, zamjeneUmjestoUlogiranogProfesora=zamjeneUmjestoUlogiranogProfesora, zamjeneDanas=zamjeneDanas, zamjeneOvajTjedan=zamjeneOvajTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, sve_obavijesti=sveObavijesti, profesor=profesor)
        elif 'Windows' in userDevice:
            return render_template("templates-pc/home.html", zamjeneIducaTriTjedna=zamjeneIducaTriTjedna, zamjeneUmjestoUlogiranogProfesora=zamjeneUmjestoUlogiranogProfesora, zamjeneDanas=zamjeneDanas, zamjeneOvajTjedan=zamjeneOvajTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, sve_obavijesti=sveObavijesti, profesor=profesor)
        else:
            return render_template("templates-pc/home.html", zamjeneIducaTriTjedna=zamjeneIducaTriTjedna, zamjeneUmjestoUlogiranogProfesora=zamjeneUmjestoUlogiranogProfesora, zamjeneDanas=zamjeneDanas, zamjeneOvajTjedan=zamjeneOvajTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, sve_obavijesti=sveObavijesti, profesor=profesor)


    elif isUserLoggedIn=="True":
        loggedInUserID = decrypt_cookie(request.cookies.get('loggedInUser'))
        loggedInUser = User.query.filter_by(id=loggedInUserID).first()

        today = date.today()
        tomarrow = today + timedelta(days=1)
        dayAfterTomarrow = tomarrow + timedelta(days=1)

        zamjeneDanas = Zamjene.query.filter(Zamjene.classroom_id==loggedInUser.classroom_id, Zamjene.datum==today).all()
        zamjeneSutra = Zamjene.query.filter(Zamjene.classroom_id==loggedInUser.classroom_id, Zamjene.datum==tomarrow).all()
        zamjenePrekosutra = Zamjene.query.filter(Zamjene.classroom_id==loggedInUser.classroom_id, Zamjene.datum==dayAfterTomarrow).all()

        daysUntilNextMonday = (-1 - today.weekday()) % 7
        nextMonday = today + timedelta(days=daysUntilNextMonday + 1)
        nextWeekStart = nextMonday
        nextWeekEnd = nextMonday + timedelta(days=6)

        zamjeneSljedeciTjedan = Zamjene.query.filter(Zamjene.datum >= nextWeekStart,Zamjene.datum <= nextWeekEnd, Zamjene.classroom_id==loggedInUser.classroom_id).order_by(Zamjene.datum).all()

        sveObavijesti = Obavjesti.query.filter(Obavjesti.school_id == loggedInUser.school_id,Obavjesti.date_added >= (datetime.utcnow() - timedelta(days=7))).order_by(Obavjesti.date_added.desc()).all()

        if 'Mobile' in userDevice:
            return render_template("templates-mobile/home_mobile.html", zamjeneDanas=zamjeneDanas, zamjeneSutra=zamjeneSutra, zamjenePrekosutra=zamjenePrekosutra, zamjeneSljedeciTjedan=zamjeneSljedeciTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, sve_obavijesti=sveObavijesti)
        elif 'Windows' in userDevice:
            return render_template("templates-pc/home.html", zamjeneDanas=zamjeneDanas, zamjeneSutra=zamjeneSutra, zamjenePrekosutra=zamjenePrekosutra, zamjeneSljedeciTjedan=zamjeneSljedeciTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, sve_obavijesti=sveObavijesti)
        else:
            return render_template("templates-pc/home.html", zamjeneDanas=zamjeneDanas, zamjeneSutra=zamjeneSutra, zamjenePrekosutra=zamjenePrekosutra, zamjeneSljedeciTjedan=zamjeneSljedeciTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, sve_obavijesti=sveObavijesti)
    else:
        if 'Mobile' in userDevice:
            return render_template("templates-mobile/start.html", zamjeneDanas=zamjeneDanas, zamjeneSutra=zamjeneSutra, zamjenePrekosutra=zamjenePrekosutra, zamjeneSljedeciTjedan=zamjeneSljedeciTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, sve_obavijesti=sveObavijesti)
        elif 'Windows' in userDevice:
            return render_template("templates-pc/start.html", zamjeneDanas=zamjeneDanas, zamjeneSutra=zamjeneSutra, zamjenePrekosutra=zamjenePrekosutra, zamjeneSljedeciTjedan=zamjeneSljedeciTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, sve_obavijesti=sveObavijesti)
        else:
            return render_template("templates-pc/start.html", zamjeneDanas=zamjeneDanas, zamjeneSutra=zamjeneSutra, zamjenePrekosutra=zamjenePrekosutra, zamjeneSljedeciTjedan=zamjeneSljedeciTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, sve_obavijesti=sveObavijesti)

@views.route('/ucenikloginhome')
def ucenikloginhome():
    userDevice = request.headers.get('User-Agent')
    isUserLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    isAdminLoggedIn = decrypt_cookie(request.cookies.get('isAdminLoggedIn'))
    isSkolaLoggedIn = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))

    sveObavijesti=[]
    zamjeneDanas=[]
    zamjeneSutra=[]
    zamjenePrekosutra=[]
    zamjeneSljedeciTjedan=[]

    if 'Mobile' in userDevice:
        return render_template("templates-mobile/startuser.html", zamjeneDanas=zamjeneDanas, zamjeneSutra=zamjeneSutra, zamjenePrekosutra=zamjenePrekosutra, zamjeneSljedeciTjedan=zamjeneSljedeciTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, sve_obavijesti=sveObavijesti)
    elif 'Windows' in userDevice:
        return render_template("templates-pc/startuser.html", zamjeneDanas=zamjeneDanas, zamjeneSutra=zamjeneSutra, zamjenePrekosutra=zamjenePrekosutra, zamjeneSljedeciTjedan=zamjeneSljedeciTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, sve_obavijesti=sveObavijesti)
    else:
        return render_template("templates-pc/startuser.html", zamjeneDanas=zamjeneDanas, zamjeneSutra=zamjeneSutra, zamjenePrekosutra=zamjenePrekosutra, zamjeneSljedeciTjedan=zamjeneSljedeciTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, sve_obavijesti=sveObavijesti)

@views.route('/skolaloginhome')
def skolaloginhome():
    userDevice = request.headers.get('User-Agent')
    isUserLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    isAdminLoggedIn = decrypt_cookie(request.cookies.get('isAdminLoggedIn'))
    isSkolaLoggedIn = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))

    sveObavijesti=[]
    zamjeneDanas=[]
    zamjeneSutra=[]
    zamjenePrekosutra=[]
    zamjeneSljedeciTjedan=[]

    if 'Mobile' in userDevice:
        return render_template("templates-mobile/startskola.html", zamjeneDanas=zamjeneDanas, zamjeneSutra=zamjeneSutra, zamjenePrekosutra=zamjenePrekosutra, zamjeneSljedeciTjedan=zamjeneSljedeciTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, sve_obavijesti=sveObavijesti)
    elif 'Windows' in userDevice:
        return render_template("templates-pc/startskola.html", zamjeneDanas=zamjeneDanas, zamjeneSutra=zamjeneSutra, zamjenePrekosutra=zamjenePrekosutra, zamjeneSljedeciTjedan=zamjeneSljedeciTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, sve_obavijesti=sveObavijesti)
    else:
        return render_template("templates-pc/startskola.html", zamjeneDanas=zamjeneDanas, zamjeneSutra=zamjeneSutra, zamjenePrekosutra=zamjenePrekosutra, zamjeneSljedeciTjedan=zamjeneSljedeciTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, sve_obavijesti=sveObavijesti)


#prikaz login page stranice
@views.route('/login')
def login():
    error=request.args.get("error")
    userDevice = request.headers.get('User-Agent')
    isUserLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    isAdminLoggedIn = decrypt_cookie(request.cookies.get('isAdminLoggedIn'))
    isSkolaLoggedIn = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))

    if 'Mobile' in userDevice:
        return render_template("templates-mobile/login.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, error=error, isLoggedIn=isUserLoggedIn)
    elif 'Windows' in userDevice:
        return render_template("templates-pc/login.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, error=error, isLoggedIn=isUserLoggedIn)
    else:
        return render_template("templates-pc/login.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, error=error, isLoggedIn=isUserLoggedIn)

#prikaz login page za admine stranice
@views.route('/loginadmin')
def loginAdmin():
    error=request.args.get("error")
    userDevice = request.headers.get('User-Agent')
    isUserLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    isAdminLoggedIn = decrypt_cookie(request.cookies.get('isAdminLoggedIn'))
    isSkolaLoggedIn = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))

    if 'Mobile' in userDevice:
        return render_template("templates-pc/login-admin.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, error=error, isLoggedIn=isUserLoggedIn)
    elif 'Windows' in userDevice:
        return render_template("templates-pc/login-admin.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, error=error, isLoggedIn=isUserLoggedIn)
    else:
        return render_template("templates-pc/login-admin.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, error=error, isLoggedIn=isUserLoggedIn)

#prikaz login page za admine stranice
@views.route('/loginskola')
def loginskola():
    error=request.args.get("error")
    userDevice = request.headers.get('User-Agent')
    isUserLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    isAdminLoggedIn = decrypt_cookie(request.cookies.get('isAdminLoggedIn'))
    isSkolaLoggedIn = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))

    if 'Mobile' in userDevice:
        return render_template("templates-mobile/login-skola.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, error=error, isLoggedIn=isUserLoggedIn)
    elif 'Windows' in userDevice:
        return render_template("templates-pc/login-skola.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, error=error, isLoggedIn=isUserLoggedIn)
    else:
        return render_template("templates-pc/login-skola.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, error=error, isLoggedIn=isUserLoggedIn)

#prikaz login page za admine stranice
@views.route('/loginskolaprof')
def loginskolaprof():
    error=request.args.get("error")
    userDevice = request.headers.get('User-Agent')
    isUserLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    isAdminLoggedIn = decrypt_cookie(request.cookies.get('isAdminLoggedIn'))
    isSkolaLoggedIn = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))

    if 'Mobile' in userDevice:
        return render_template("templates-mobile/login-skola-profesor.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, error=error, isLoggedIn=isUserLoggedIn)
    elif 'Windows' in userDevice:
        return render_template("templates-pc/login-skola-profesor.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, error=error, isLoggedIn=isUserLoggedIn)
    else:
        return render_template("templates-pc/login-skola-profesor.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, error=error, isLoggedIn=isUserLoggedIn)

#prikaz register page stranice
@views.route('/register')
def register():
    error=request.args.get("error")
    userDevice = request.headers.get('User-Agent')
    isUserLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    isAdminLoggedIn = decrypt_cookie(request.cookies.get('isAdminLoggedIn'))
    isSkolaLoggedIn = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))

    if 'Mobile' in userDevice:
        return render_template("templates-mobile/register.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, error=error, isLoggedIn=isUserLoggedIn)
    elif 'Windows' in userDevice:
        return render_template("templates-pc/register.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, error=error, isLoggedIn=isUserLoggedIn)
    else:
        return render_template("templates-pc/register.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, error=error, isLoggedIn=isUserLoggedIn)

#prikaz menu-a za dodavanje skola
@views.route('/add-school-menu', methods=['GET', 'POST'])
def addschoolmenu():
    error=request.args.get("error")
    isUserLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    isAdminLoggedIn = decrypt_cookie(request.cookies.get('isAdminLoggedIn'))
    isSkolaLoggedIn = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
    if isAdminLoggedIn:
        return render_template("templates-pc/add-school-menu.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, error=error, isLoggedIn=isUserLoggedIn)
    else:
        return redirect("/")

#prikaz menu za administraciju skole
@views.route('/skolamenu', methods=['GET', 'POST'])
def skolamenu():
    isUserLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    userDevice = request.headers.get('User-Agent')
    isAdminLoggedIn = decrypt_cookie(request.cookies.get('isAdminLoggedIn'))
    isSkolaLoggedIn = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
    loggedInSkolaID = int(decrypt_cookie(request.cookies.get('loggedInSchoolID')))
    loggedInProfID = decrypt_cookie(request.cookies.get('loggedInProfesorID'))
    if loggedInProfID:
        loggedInProfID = int(decrypt_cookie(request.cookies.get('loggedInProfesorID')))
    loggedInSkola = School.query.filter_by(id=loggedInSkolaID).first()
    profesor = Profesor.query.filter_by(id=loggedInProfID).first()

    obavijesti = Obavjesti.query.filter(Obavjesti.school_id == loggedInSkolaID,Obavjesti.date_added >= (datetime.utcnow() - timedelta(days=7))).order_by(Obavjesti.date_added.desc()).all()

    if isUserLoggedIn and isSkolaLoggedIn:
        classrooms = Classroom.query.filter_by(school_id=loggedInSkolaID).all()
        classrooms = sorted(classrooms, key=lambda x: x.name)
        if 'Mobile' in userDevice:
            return render_template("templates-mobile/skola-menu.html", admin=isAdminLoggedIn, Skola=isSkolaLoggedIn, skola=loggedInSkola, isLoggedIn=isUserLoggedIn, classrooms=classrooms, obavijesti=obavijesti, profesor=profesor)
        elif 'Windows' in userDevice:
            return render_template("templates-pc/skola-menu.html", admin=isAdminLoggedIn, Skola=isSkolaLoggedIn, skola=loggedInSkola, isLoggedIn=isUserLoggedIn, classrooms=classrooms, obavijesti=obavijesti, profesor=profesor)
        else:
            return render_template("templates-pc/skola-menu.html", admin=isAdminLoggedIn, Skola=isSkolaLoggedIn, skola=loggedInSkola, isLoggedIn=isUserLoggedIn, classrooms=classrooms, obavijesti=obavijesti, profesor=profesor)

    else:
        return redirect("/")

#prikaz menu za administraciju skole
@views.route('/skolaadminmenu', methods=['GET', 'POST'])
def skolaadminmenu():
    isUserLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    userDevice = request.headers.get('User-Agent')
    isAdminLoggedIn = decrypt_cookie(request.cookies.get('isAdminLoggedIn'))
    isSkolaLoggedIn = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
    loggedInSkolaID = int(decrypt_cookie(request.cookies.get('loggedInSchoolID')))
    loggedInSkola = School.query.filter_by(id=loggedInSkolaID).first()

    if isUserLoggedIn and isSkolaLoggedIn:
        profesori = Profesor.query.filter_by(school_id=loggedInSkolaID).order_by(asc(Profesor.name)).all()
        if 'Mobile' in userDevice:
            return render_template("templates-mobile/skola-admin-menu.html", admin=isAdminLoggedIn, Skola=isSkolaLoggedIn, skola=loggedInSkola, isLoggedIn=isUserLoggedIn, profesori=profesori)
        elif 'Windows' in userDevice:
            return render_template("templates-pc/skola-admin-menu.html", admin=isAdminLoggedIn, Skola=isSkolaLoggedIn, skola=loggedInSkola, isLoggedIn=isUserLoggedIn, profesori=profesori)
        else:
            return render_template("templates-pc/skola-admin-menu.html", admin=isAdminLoggedIn, Skola=isSkolaLoggedIn, skola=loggedInSkola, isLoggedIn=isUserLoggedIn, profesori=profesori)

    else:
        return redirect("/")

#prikaz profila ucenika
@views.route('/viewprofileuser', methods=['GET'])
def viewprofileuser():
    userDevice = request.headers.get('User-Agent')
    isSkolaLoggedIn=request.args.get("skola")
    loggedInUser = User.query.filter_by(id=int(decrypt_cookie(request.cookies.get('loggedInUser')))).first()
    isUserLoggedIn=request.args.get("isLoggedIn")
    isAdminLoggedIn = decrypt_cookie(request.cookies.get('isAdminLoggedIn'))

    if 'Mobile' in userDevice:
        return render_template("templates-mobile/profile.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, user=loggedInUser, isLoggedIn=isUserLoggedIn)
    elif 'Windows' in userDevice:
        return render_template("templates-pc/profile.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, user=loggedInUser, isLoggedIn=isUserLoggedIn)
    else:
        return render_template("templates-pc/profile.html", admin=isAdminLoggedIn, skola=isSkolaLoggedIn, user=loggedInUser, isLoggedIn=isUserLoggedIn)

#randomiziranje id-ova svih korisnika
@views.route('/resetusersid', methods=['GET', 'POST'])
def resetusersid():
    allusers = User.query.all()
    for i in allusers:
        randomID=random.randint(1000,100000)
        while User.query.filter_by(id=randomID).first():
            randomID=random.randint(1000,100000)
        i.id = randomID
        db.session.commit()
    return redirect(url_for("views.home"))

#logika za registriranje novog racuna i dodavanje tog racuna u databazu
@views.route('/registersend', methods=['GET', 'POST'])
def registersend():
    if request.method=="POST":
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        password = request.form['password']
        schoolID = request.form['schoolID']
        classID = request.form['classID']

        #provjera jesu li uneseni podatci valjani

        #provjera emaila
        if len(email)>5 and "@" in email and "." in email and len(email)<50:
            pass
        else:
            error="Nevaljani email."
            return redirect(url_for("views.register", error=error))

        #provjera lozinke
        hasGotLetter = any(char.isalpha() for char in password)
        hasGotNumber = any(char.isdigit() for char in password)
        if len(password)>=8 and len(password)<51:
            if hasGotLetter and hasGotNumber:
                pass
            else:
                error="Loznika mora sadržavati i brojeve i slova."
                return redirect(url_for("views.register", error=error))
        else:
            error="Lozinka mora sadržavati barem 8 znakova."
            return redirect(url_for("views.register", error=error))

        #provjera ID-a skole
        if len(schoolID)!=0 and len(schoolID)<20:
            try:
                int(schoolID)
                pass
            except ValueError:
                error="Nevaljan ID Škole."
                return redirect(url_for("views.register", error=error))

        #provjera ID-a ucionice
        if len(classID)!=0 and len(classID)<20:
            try:
                int(classID)
                pass
            except ValueError:
                error="Nevaljan ID učionice."
                return redirect(url_for("views.register", error=error))


        #provjera postoji li račun s tim emailom
        user = User.query.filter_by(email=email).first()
        if user:
            error="Korisnik s tim emailom već postoji."
            return redirect(url_for("views.register", error=error))
        else:

            randomID = random.randint(1000,100000)
            user = User.query.filter_by(id=randomID).first()
            while user:
                randomID = random.randint(1000,100000)
                user = User.query.filter_by(id=randomID).first()
            newUser = User(id=randomID, name = name, lastname=surname, email=email, password=generate_password_hash(password, method='pbkdf2:sha256'), school_id=schoolID, classroom_id=classID)
            db.session.add(newUser)
            db.session.commit()

            #login novog usera
            user = User.query.filter_by(email=email).first()
            response = make_response(redirect("/"))
            response.set_cookie('isUserLoggedIn', value=cipher_suite.encrypt(b"True").decode(), samesite='Strict', httponly=True)
            response.set_cookie('loggedInUser', value=cipher_suite.encrypt(str(user.id).encode()).decode(), samesite='Strict', httponly=True)
            return response

#logika za ulogiravanje korisnika
@views.route('/loginsend', methods=['POST'])
def loginsend():
    error=""

    email = request.form['email']
    password = request.form['password']
    user = User.query.filter_by(email=email).first()
    if user:
        if check_password_hash(user.password, password):
            response = make_response(redirect("/"))
            response.set_cookie('isUserLoggedIn', value=cipher_suite.encrypt(b"True").decode(), samesite='Strict', httponly=True)
            response.set_cookie('loggedInUser', value=cipher_suite.encrypt(str(user.id).encode()).decode(), samesite='Strict', httponly=True)
            return response
        else:
            error="Kriva lozinka."
            response = make_response(redirect(url_for("views.login", error=error)))
            response.set_cookie('isUserLoggedIn', value=cipher_suite.encrypt(b"False").decode(), samesite='Strict', httponly=True)
            return response
    else:
        error="Krivi email."
        response = make_response(redirect(url_for("views.login", error=error)))
        response.set_cookie('isUserLoggedIn', value=cipher_suite.encrypt(b"False").decode(), samesite='Strict', httponly=True)
        return response

#logika za ulogiravanje admina
@views.route('/loginadminsend', methods=['POST'])
def loginadminsend():
    error=""
    password = request.form['password']
    if password=="UNxOc7eP3j7mv6nRRhk3TFhAMjTdisR7ZzrAxwimBR38zZEdFH":
        response = make_response(redirect("/add-school-menu"))
        response.set_cookie('isAdminLoggedIn', value=cipher_suite.encrypt(b"True").decode(), samesite='Strict', httponly=True)
        return response
    else:
        error="Kriva lozinka."
        return redirect(url_for("views.loginAdmin", error=error))

#logika za ulogiravanje administracije skola
@views.route('/loginskolasend', methods=['GET', 'POST'])
def loginskolasend():
    error=""
    prof = request.form['prof']
    if prof=="da":
        idskola = request.form['id-skola']
        school = School.query.filter_by(id=idskola).first()
        if school:
            id = request.form['id-prof']
            prof = Profesor.query.filter_by(id=id).first()
            if prof:
                pin = request.form['pin']
                pravipin = prof.pin
                try:
                    pin_as_int = int(pin)
                except ValueError:
                    error = "PIN mora biti broj!"
                    response = make_response(redirect(url_for("views.loginskolaprof", error=error)))
                    response.set_cookie('isUserLoggedIn', value=cipher_suite.encrypt(b"False").decode(), samesite='Strict', httponly=True)
                    return response
                else:
                    if pin_as_int==pravipin:
                        if school.id==prof.school_id:
                            response = make_response(redirect("/"))
                            response.set_cookie('isUserLoggedIn', value=cipher_suite.encrypt(b"True").decode(), samesite='Strict', httponly=True)
                            response.set_cookie('isSkolaLoggedIn', value=cipher_suite.encrypt(b"True").decode(), samesite='Strict', httponly=True)
                            response.set_cookie('loggedInSchoolID', value=cipher_suite.encrypt(str(idskola).encode()).decode(), samesite='Strict', httponly=True)
                            response.set_cookie('loggedInProfesorID', value=cipher_suite.encrypt(str(id).encode()).decode(), samesite='Strict', httponly=True)
                            return response
                        else:
                            error="Profesor i škola se ne podudaraju!"
                            response = make_response(redirect(url_for("views.loginskolaprof", error=error)))
                            response.set_cookie('isUserLoggedIn', value=cipher_suite.encrypt(b"False").decode(), samesite='Strict', httponly=True)
                            return response
                    else:
                        error="Krivi PIN."
                        response = make_response(redirect(url_for("views.loginskolaprof", error=error)))
                        response.set_cookie('isUserLoggedIn', value=cipher_suite.encrypt(b"False").decode(), samesite='Strict', httponly=True)
                        return response
            else:
                error = "Profesor s tim ID-om ne postoji!"
                response = make_response(redirect(url_for("views.loginskolaprof", error=error)))
                response.set_cookie('isUserLoggedIn', value=cipher_suite.encrypt(b"False").decode(), samesite='Strict', httponly=True)
                return response
        else:
            error="Krivi ID škole."
            response = make_response(redirect(url_for("views.loginskolaprof", error=error)))
            response.set_cookie('isUserLoggedIn', value=cipher_suite.encrypt(b"False").decode(), samesite='Strict', httponly=True)
            return response
    elif prof=="ne":
        id = request.form['id']
        school = School.query.filter_by(id=id).first()
        if school:
            instertedpassword = request.form['password']
            password=school.login_password
            if check_password_hash(password, instertedpassword):
                response = make_response(redirect("/skolaadminmenu"))
                response.set_cookie('isUserLoggedIn', value=cipher_suite.encrypt(b"True").decode(), samesite='Strict', httponly=True)
                response.set_cookie('isSkolaLoggedIn', value=cipher_suite.encrypt(b"True").decode(), samesite='Strict', httponly=True)
                response.set_cookie('loggedInSchoolID', value=cipher_suite.encrypt(str(id).encode()).decode(), samesite='Strict', httponly=True)
                return response
            else:
                error="Kriva lozinka."
                response = make_response(redirect(url_for("views.loginskola", error=error)))
                response.set_cookie('isUserLoggedIn', value=cipher_suite.encrypt(b"False").decode(), samesite='Strict', httponly=True)
                return response
        else:
            error="Krivi ID škole."
            response = make_response(redirect(url_for("views.loginskola", error=error)))
            response.set_cookie('isUserLoggedIn', value=cipher_suite.encrypt(b"False").decode(), samesite='Strict', httponly=True)
            return response

#logika za izlogiravanje
@views.route('/logout')
def logout():
    response = make_response(redirect("/"))
    cookies_to_delete = request.cookies.keys()
    for cookie_name in cookies_to_delete:
        response.delete_cookie(cookie_name)
    return response

#logika za dodavanje novog razreda
@views.route('/dodajrazred', methods=['GET', 'POST'])
def dodajrazred():
        classroom_name = request.form.get('classroom_name')
        razrednik = request.form.get('razrednik')
        loggedInSkolaID = int(decrypt_cookie(request.cookies.get('loggedInSchoolID')))
        characters = string.digits
        id = int(''.join(random.choice(characters) for _ in range(8)))
        while Classroom.query.filter_by(id=id).first():
            id = int(''.join(random.choice(characters) for _ in range(8)))
        db.session.add(Classroom(name=classroom_name, school_id=loggedInSkolaID, id=id, razrednik=razrednik))
        db.session.commit()
        return redirect(url_for("views.skolamenu"))

#logika za prikaz profila
@views.route('/viewprofile')
def viewprofile():
    isSkolaLoggedIn = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
    isUserLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    if isSkolaLoggedIn=="True":
        return redirect("/skolamenu")
    else:
        return redirect(url_for("views.viewprofileuser", skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn))

#stranica za dodavanje skola
@views.route('/addschooladmin', methods=['GET', 'POST'])
def addschool():
    isLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    #prikaz stranice i provjera jesi li ulogiran kao admin
    if request.method=="GET":
        isAdminLoggedIn = decrypt_cookie(request.cookies.get('isAdminLoggedIn'))
        if isAdminLoggedIn:
            return redirect("/add-school-menu")
        else:
            error=request.args.get("error")
            user_agent = request.headers.get('User-Agent')
            skola = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
            if 'Mobile' in user_agent:
                return render_template("templates-mobile/add-school-login.html", admin=isAdminLoggedIn, skola=skola, error=error, isLoggedIn=isLoggedIn)
            elif 'Windows' in user_agent:
                return render_template("templates-pc/add-school-login.html",admin=isAdminLoggedIn, skola=skola, error=error, isLoggedIn=isLoggedIn)
            else:
                return render_template("templates-pc/add-school-login.html",admin=isAdminLoggedIn, skola=skola, error=error, isLoggedIn=isLoggedIn)
    #logika za ulogiravanje kao admin
    elif request.method=="POST":
        password = request.form['password']

        if password=="lozinka":
            response = make_response(redirect("/add-school-menu"))
            response.set_cookie('isUserLoggedIn', value=cipher_suite.encrypt(b"True").decode(), samesite='Strict', httponly=True)
            response.set_cookie('isAdminLoggedIn', value=cipher_suite.encrypt(b"True").decode(), samesite='Strict', httponly=True)
            return response
        else:
            error="Kriva lozinka."
            response = make_response(redirect(url_for("views.addschool", error=error)))
            response.set_cookie('isUserLoggedIn', value=cipher_suite.encrypt(b"False").decode(), samesite='Strict', httponly=True)
            response.set_cookie('isAdminLoggedIn', value=cipher_suite.encrypt(b"False").decode(), samesite='Strict', httponly=True)
            return response

#logika za dodavanje skole
@views.route('/addschoolfunction', methods=['GET', 'POST'])
def addschoolfunction():
    if request.method=="POST":
        name = request.form['name']
        password = request.form['password']
        characters = string.digits
        id = int(''.join(random.choice(characters) for _ in range(8)))
        while School.query.filter_by(id=id).first():
            id = int(''.join(random.choice(characters) for _ in range(8)))

        has_letter = any(char.isalpha() for char in password)
        has_number = any(char.isdigit() for char in password)
        if len(password)>=8:
            if has_letter and has_number:
                pass
            else:
                error="Loznika mora sadržavati i brojeve i slova."
                return redirect(url_for("views.addschoolmenu", error=error))
        else:
            error="Lozinka mora sadržavati barem 8 znakova."
            return redirect(url_for("views.addschoolmenu", error=error))


        #provjera postoji li račun s tim emailom
        existing_user = School.query.filter_by(id=id).first()
        if existing_user:
            error="Korisnik s tim emailom već postoji."
            return redirect(url_for("views.addschoolmenu", error=error))
        else:
            newSchool = School(name = name, login_password=generate_password_hash(password, method='pbkdf2:sha256'), id=id)
            db.session.add(newSchool)
            db.session.commit()

            #login novog usera
            school = School.query.filter_by(id=id).first()
            response = make_response(redirect("/"))
            response.set_cookie('isSkolaLoggedIn', value=cipher_suite.encrypt(b"True").decode(), samesite='Strict', httponly=True)
            response.set_cookie('isAdminLoggedIn', value=cipher_suite.encrypt(b"False").decode(), samesite='Strict', httponly=True)
            response.set_cookie('loggedInSchoolID', value=cipher_suite.encrypt(str(school.id).encode()).decode(), samesite='Strict', httponly=True)
            return response


#prikaz stranice za dodavanje i uredivanje zamjena za satnicare
@views.route('/prikazizamjene', methods=['GET', 'POST'])
def prikazizamjene():
    error=request.args.get("error")
    user_agent = request.headers.get('User-Agent')
    isLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    skola = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
    loggedInSkolaID = int(decrypt_cookie(request.cookies.get('loggedInSchoolID')))
    svirazredi = Classroom.query.filter_by(school_id=loggedInSkolaID).all()
    svipredmeti = Predmeti.query.filter_by(school_id=loggedInSkolaID).all()
    sviprofesori = Profesor.query.filter_by(school_id=loggedInSkolaID).all()
    sviprofesori = []
    predmetistrings = []
    sve_zamjene = Zamjene.query.filter(Zamjene.school_id == loggedInSkolaID, Zamjene.date_added >= (datetime.utcnow() - timedelta(days=28))).order_by(desc(Zamjene.datum), Zamjene.classroom_id).all()
    for predmet in svipredmeti:
        prof = Profesor.query.filter_by(id=predmet.profesor).first().name
        if prof not in sviprofesori:
            sviprofesori += [prof]
        predmetistrings += [(predmet.predmet + " | " + prof, predmet.profesor)]

    sviprofesori = sorted(sviprofesori)
    svirazredi = sorted(svirazredi, key=lambda x: x.name)
    predmetistrings = sorted(predmetistrings)
    loggedInProfID = int(decrypt_cookie(request.cookies.get('loggedInProfesorID')))
    profesor = Profesor.query.filter_by(id=loggedInProfID).first()

    if 'Mobile' in user_agent:
        return render_template("templates-mobile/prikaz-zamjena.html", skola=skola, error=error, isLoggedIn=isLoggedIn, profesori=sviprofesori, predmeti=predmetistrings, razredi=svirazredi, sve_zamjene=sve_zamjene, school_id=loggedInSkolaID, profesor=profesor)

    elif 'Windows' in user_agent:
        return render_template("templates-pc/prikaz-zamjena.html", skola=skola, error=error, isLoggedIn=isLoggedIn, profesori=sviprofesori, predmeti=predmetistrings, razredi=svirazredi, sve_zamjene=sve_zamjene, school_id=loggedInSkolaID, profesor=profesor)

    else:
        return render_template("templates-pc/prikaz-zamjena.html", skola=skola, error=error, isLoggedIn=isLoggedIn, profesori=sviprofesori, predmeti=predmetistrings, razredi=svirazredi, sve_zamjene=sve_zamjene, school_id=loggedInSkolaID, profesor=profesor)

#logika za dodavanje zamjene
@views.route('/dodajzamjenu', methods=['GET', 'POST'])
def dodajzamjenu():
    if request.method=="POST":
        loggedInSkolaID = int(decrypt_cookie(request.cookies.get('loggedInSchoolID')))
        loggedInProfID = int(decrypt_cookie(request.cookies.get('loggedInProfesorID')))
        #prikupljanje podataka o zamjeni
        zamjenaza = request.form['zamjenaza']

        datum = request.form['date']
        datum = request.form['date']
        date_components = datum.split('-')
        datum = '-'.join(date_components[::-1])
        datum = datetime.strptime(datum, '%d-%m-%Y').date()

        od = request.form['from']
        do = ""

        if 'to' in request.form:
            od = od[:2] + ' i ' + str(int(od[0])+1)+ '. sat'

        classroomID = request.form['razred']
        classroom_name = Classroom.query.filter_by(id=classroomID).first().name

        #slanje obavijesti za ucenike tog razreda
        allUsersOfClassroom = User.query.filter_by(classroom_id=classroomID).all()
        for user in allUsersOfClassroom:
            threading.Thread(target=send_email_in_context, args=(current_app._get_current_object(), user.email, 'Dodana je nova zamjena', "Imaš novu zamjenu. Pogledaj ju na zamjene.hr")).start()

        #prikuljanje profesora kojima se mora poslati mail
        broj_novih_predmeta = int(request.form['broj-novih-predmeta'])
        novi_predmet_values = [request.form[f'novipredmet{i}'] for i in range(1, broj_novih_predmeta + 1)]
        profesori_za_obavijest=[]
        for i in novi_predmet_values:
            if i!="Slobodan Sat, 0":
                profesor_id_str = i[i.find(",") + 3 : -2]
                profesori_za_obavijest+=[int(profesor_id_str)]

        #azuriranje popisa predmeta za prikaz
        for i in range(len(novi_predmet_values)):
            if novi_predmet_values[i]!="Slobodan Sat, 0":
                novi_predmet_values[i] = novi_predmet_values[i][2:novi_predmet_values[i].find(",")-1]
            else:
                novi_predmet_values[i] = "| Slobodan Sat |"

        #slanje obavijesti profesorima
        allProfesorsInSchool = Profesor.query.filter_by(school_id=loggedInSkolaID).all()
        for user in allProfesorsInSchool:
            if user.email != "noemail" and user.id in profesori_za_obavijest:

                threading.Thread(target=send_email_in_context, args=(current_app._get_current_object(), user.email, 'Dodana je nova zamjena', "Dana: " + datum.strftime('%d-%m-%Y') + " ćeš imati " + classroom_name + " " + od + ".")).start()
                time.sleep(0.5)

        #slanje obavijesti profesoru koji nece imati nastavu
        novi_predmet_string = ' - '.join(novi_predmet_values)

        biljeska = request.form['biljeska']

        dodao_profesor = loggedInProfID

        zamjenazaProf = Profesor.query.filter_by(school_id=loggedInSkolaID, name=zamjenaza).first()
        if zamjenazaProf:
            if zamjenazaProf.email!="noemail":
                threading.Thread(target=send_email_in_context, args=(current_app._get_current_object(), zamjenazaProf.email, 'Nova zamjena na zamjene.hr', "Dana: " + datum.strftime('%d-%m-%Y') + " nećeš imati " + classroom_name + " " + od + ".")).start()

        #dodavanje zamjene u databazu
        nova_zamjena = Zamjene(od=od, do=do, datum=datum, zamjena=novi_predmet_string, classroom_id=classroomID, stariprofesor=zamjenaza, school_id=loggedInSkolaID, classroom_name=classroom_name, biljeska=biljeska, dodao_profesor=dodao_profesor)
        db.session.add(nova_zamjena)
        db.session.commit()


    return redirect(url_for("views.prikazizamjene"))

#brisanje zamjene
@views.route('/delete_zamjene/<int:zamjene_id>', methods=['POST'])
def delete_zamjene(zamjene_id):
    error=request.args.get("error")
    isLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))

    zamjene = Zamjene.query.get(zamjene_id)

    db.session.delete(zamjene)
    db.session.commit()

    schoolID = request.form['school_id']
    classroomID = request.form['classroom_id']
    classroom = Classroom.query.filter_by(id=classroomID, school_id=schoolID).first()
    zamjene = Zamjene.query.filter_by(classroom_id=classroomID).all()

    return redirect(url_for("views.prikazizamjene", error=error, isLoggedIn=isLoggedIn, sve_zamjene=zamjene, razred=classroom, classroomid=classroomID, schoolid=schoolID))


#brisanje razreda
@views.route('/obrisirazred', methods=['POST'])
def obriširazred():
    schoolID = request.form['school_id']
    classroomID = request.form['classroom_id']
    classroom = Classroom.query.filter_by(id=classroomID, school_id=schoolID).first()
    sve_zamjene = Zamjene.query.filter(Zamjene.classroom_name==classroom.name, Zamjene.school_id==schoolID).all()
    for i in sve_zamjene:
        db.session.delete(i)
    User.query.filter_by(classroom_id=classroomID).update({'classroom_id': ""})

    db.session.delete(classroom)
    db.session.commit()

    return redirect("/skolamenu")

#dodavanje obavijesti
@views.route('/addad', methods=['POST','GET'])
def addad():
    schoolID = int(decrypt_cookie(request.cookies.get('loggedInSchoolID')))
    loggedInProfID = int(decrypt_cookie(request.cookies.get('loggedInProfesorID')))
    msg = request.form['content']
    name = request.form['name']
    dodao_profesor = loggedInProfID

    obavijest = Obavjesti(school_id=schoolID, name=name, content=msg, dodao_profesor=dodao_profesor)

    #slanje obavijesti ucenicima
    allUsers = User.query.filter_by(school_id=schoolID).all()
    for user in allUsers:
        threading.Thread(target=send_email_in_context, args=(current_app._get_current_object(), user.email, 'Dodana je nova obavijest', "Imaš novu obavijest. Pogledaj ju na zamjene.hr")).start()

    #slanje obavijesti profesorima
    allProfesors = Profesor.query.filter_by(school_id=schoolID).all()
    for profesor in allProfesors:
        if profesor.email!="noemail":
            threading.Thread(target=send_email_in_context, args=(current_app._get_current_object(), user.email, 'Dodana je nova obavijest', "Imaš novu obavijest. Pogledaj ju na zamjene.hr")).start()

    #dodavanje obavijesti u databazu
    db.session.add(obavijest)
    db.session.commit()

    return redirect("/skolamenu")

#brisanje obavijesti
@views.route('/obrisiobavijest', methods=['POST'])
def obrisiobavijest():
    school_id = request.form.get('school_id')
    obavijest_id = request.form.get('obavijest_id')

    obavijest = Obavjesti.query.filter_by(school_id=school_id, id=obavijest_id).first()

    db.session.delete(obavijest)
    db.session.commit()

    return redirect("/skolamenu")

#dodavanje rasporeda za jutarnju smjenu
@views.route('/dodajraspored/', methods=['GET', 'POST'])
def dodajraspored():
    error=request.args.get("error")
    user_agent = request.headers.get('User-Agent')
    isLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    skola = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
    loggedInProfID = int(decrypt_cookie(request.cookies.get('loggedInProfesorID')))
    profesor = Profesor.query.filter_by(id=loggedInProfID).first()
    #prikaz stranice rasporeda
    if request.method=='GET':
        classroom_id = request.args.get('classroom_id')
        raspored_sati = RasporedSati.query.filter_by(classroom_id=classroom_id).first()
        if raspored_sati:
            raspored_string = raspored_sati.raspored_string
        else:
            raspored_string = ","*45
        data = raspored_string.split(',')
        raspored_sati_popodne = RasporedSatiPopodne.query.filter_by(classroom_id=classroom_id).first()
        if raspored_sati_popodne:
            raspored_string = raspored_sati_popodne.raspored_string
        else:
            raspored_string = ","*45
        data1 = raspored_string.split(',')

        if 'Mobile' in user_agent:
            return render_template('templates-mobile/dodaj-raspored.html', skola=skola, data1=data1, data=data, classroom_id=classroom_id, isLoggedIn=isLoggedIn, error=error, profesor=profesor)
        elif 'Windows' in user_agent:
            return render_template('templates-pc/dodaj-raspored.html', skola=skola, data1=data1, data=data, classroom_id=classroom_id, isLoggedIn=isLoggedIn, error=error, profesor=profesor)
        else:
            return render_template('templates-pc/dodaj-raspored.html', skola=skola, data1=data1, data=data, classroom_id=classroom_id, isLoggedIn=isLoggedIn, error=error, profesor=profesor)


    #logika za dodavanje rasporeda
    elif request.method == 'POST':
        data = []
        for i in range(9):
            for j in range(5):
                input_name = "predmet_" + str(i) + "_" + str(j)
                predmet_value = request.form.get(input_name)
                data.append(predmet_value)

        classroom_id = request.form['classroom_id']
        raspored_sati = RasporedSati.query.filter_by(classroom_id=classroom_id).first()

        if raspored_sati:
            existing_raspored_string = raspored_sati.raspored_string
        else:
            existing_raspored_string = ","*45
        existing_raspored_data = existing_raspored_string.split(',')

        #brisanje djelova iz rasporeda
        new_data = []
        for i in range(len(data)):
            if data[i]=="x" or data[i]=="X":
                new_data.append("")
            elif data[i]!="" and data[i]!=existing_raspored_data[i]:
                new_data.append(data[i])
            else:
                new_data.append(existing_raspored_data[i])

        items_string = ','.join(new_data)
        new_raspored_sati = RasporedSati(classroom_id=classroom_id, raspored_string=items_string)

        existing_raspored_sati = RasporedSati.query.filter_by(classroom_id=classroom_id).first()
        if existing_raspored_sati:
            db.session.delete(existing_raspored_sati)

        db.session.add(new_raspored_sati)
        db.session.commit()

        raspored_sati_popodne = RasporedSatiPopodne.query.filter_by(classroom_id=classroom_id).first()
        if raspored_sati_popodne:
            raspored_string = raspored_sati_popodne.raspored_string
        else:
            raspored_string = ","*45
        data1 = raspored_string.split(',')

        if 'Mobile' in user_agent:
            return render_template('templates-mobile/dodaj-raspored.html', skola=skola, data1=data1, data=new_data, classroom_id=classroom_id, isLoggedIn=isLoggedIn, error=error, profesor=profesor)
        elif 'Windows' in user_agent:
            return render_template('templates-pc/dodaj-raspored.html', skola=skola, data1=data1, data=new_data, classroom_id=classroom_id, isLoggedIn=isLoggedIn, error=error, profesor=profesor)
        else:
            return render_template('templates-pc/dodaj-raspored.html', skola=skola, data1=data1, data=new_data, classroom_id=classroom_id, isLoggedIn=isLoggedIn, error=error, profesor=profesor)

#logika za dodavanje rasporeda za popodnevnu smjenu
@views.route('/dodajrasporedpopodne/', methods=[ 'POST'])
def dodajrasporedpopodne():
    error=request.args.get("error")
    user_agent = request.headers.get('User-Agent')
    isLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    skola = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
    loggedInProfID = int(decrypt_cookie(request.cookies.get('loggedInProfesorID')))
    profesor = Profesor.query.filter_by(id=loggedInProfID).first()


    if request.method == 'POST':
        data = []
        for i in range(9):
            for j in range(5):
                input_name = "predmet1_" + str(i) + "_" + str(j)
                predmet_value = request.form.get(input_name)
                data.append(predmet_value)

        classroom_id = request.form['classroom_id']
        raspored_sati = RasporedSatiPopodne.query.filter_by(classroom_id=classroom_id).first()

        if raspored_sati:
            existing_raspored_string = raspored_sati.raspored_string
        else:
            existing_raspored_string = ","*45
        existing_raspored_data = existing_raspored_string.split(',')

        #brisanje djelova starog rasporeda
        new_data = []
        for i in range(len(data)):
            if data[i]=="x" or data[i]=="X":
                new_data.append("")
            elif data[i]!="" and data[i]!=existing_raspored_data[i]:
                new_data.append(data[i])
            else:
                new_data.append(existing_raspored_data[i])

        items_string = ','.join(new_data)
        new_raspored_sati = RasporedSatiPopodne(classroom_id=classroom_id, raspored_string=items_string)

        existing_raspored_sati = RasporedSatiPopodne.query.filter_by(classroom_id=classroom_id).first()
        if existing_raspored_sati:
            db.session.delete(existing_raspored_sati)

        db.session.add(new_raspored_sati)
        db.session.commit()

        raspored_sati = RasporedSati.query.filter_by(classroom_id=classroom_id).first()
        if raspored_sati:
            raspored_string = raspored_sati.raspored_string
        else:
            raspored_string = ","*45
        data = raspored_string.split(',')

        if 'Mobile' in user_agent:
            return render_template('templates-mobile/dodaj-raspored.html', skola=skola, data1=new_data, data=data, classroom_id=classroom_id, isLoggedIn=isLoggedIn, error=error, profesor=profesor)
        elif 'Windows' in user_agent:
            return render_template('templates-pc/dodaj-raspored.html', skola=skola, data1=new_data, data=data, classroom_id=classroom_id, isLoggedIn=isLoggedIn, error=error, profesor=profesor)
        else:
            return render_template('templates-pc/dodaj-raspored.html', skola=skola, data1=new_data, data=data, classroom_id=classroom_id, isLoggedIn=isLoggedIn, error=error, profesor=profesor)


#prikaz i dodavanje rasporeda ucionica ujutro
@views.route('/update_table/', methods=['GET', 'POST'])
def update_table():
    error=request.args.get("error")
    isLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    user_agent = request.headers.get('User-Agent')
    skola = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
    loggedInProfID = int(decrypt_cookie(request.cookies.get('loggedInProfesorID')))
    profesor = Profesor.query.filter_by(id=loggedInProfID).first()
    #prikaz rasporeda ucionica
    if request.method=='GET':
        school_id = request.args.get('school_id')
        raspored = RasporedUcionica.query.filter_by(school_id=school_id).first()
        if raspored:
            raspored_string = raspored.raspored_string
        else:
            raspored_string = ","*1125
        data = raspored_string.split(',')

        raspored = RasporedUcionicaPopodne.query.filter_by(school_id=school_id).first()
        if raspored:
            raspored_string = raspored.raspored_string
        else:
            raspored_string = ","*1125
        data1 = raspored_string.split(',')

        if 'Mobile' in user_agent:
            return render_template('templates-mobile/rasporeducionica.html', skola=skola, data1=data1, data=data, school_id=school_id, isLoggedIn=isLoggedIn, error=error, profesor=profesor)
        elif 'Windows' in user_agent:
            return render_template('templates-pc/rasporeducionica.html', skola=skola, data1=data1, data=data, school_id=school_id, isLoggedIn=isLoggedIn, error=error, profesor=profesor)
        else:
            return render_template('templates-pc/rasporeducionica.html', skola=skola, data1=data1, data=data, school_id=school_id, isLoggedIn=isLoggedIn, error=error, profesor=profesor)

    #logika za dodavanje i uredivanje rasporeda ucionica
    elif request.method == 'POST':
        data = []
        for i in range(25):
            for j in range(45):
                input_name = "razred_" + str(i) + "_" + str(j)
                razred_value = request.form.get(input_name)
                if razred_value!=None:
                    data.append(razred_value)
        school_id = request.form['school_id']
        raspored = RasporedUcionica.query.filter_by(school_id=school_id).first()

        if raspored:
            existing_raspored_string = raspored.raspored_string
        else:
            existing_raspored_string = ","*1125
        existing_raspored_data = existing_raspored_string.split(',')

        #brisanje djelova starog rasporeda
        new_data = []
        for i in range(len(data)):
            if data[i]=="x" or data[i]=="X":
                new_data.append("")
            elif data[i]!="" and data[i]!=existing_raspored_data[i]:
                new_data.append(data[i])
            else:
                new_data.append(existing_raspored_data[i])

        items_string = ','.join(new_data)
        new_raspored = RasporedUcionica(raspored_string=items_string, school_id=school_id)

        existing_raspored = RasporedUcionica.query.filter_by(school_id=school_id).first()
        if existing_raspored:
            db.session.delete(existing_raspored)

        db.session.add(new_raspored)
        db.session.commit()

        raspored = RasporedUcionicaPopodne.query.filter_by(school_id=school_id).first()
        if raspored:
            raspored_string = raspored.raspored_string
        else:
            raspored_string = ","*1125
        data1 = raspored_string.split(',')


        if 'Mobile' in user_agent:
            return render_template('templates-mobile/rasporeducionica.html', skola=skola, school_id=school_id, data1=data1, data=new_data, isLoggedIn=isLoggedIn, error=error, profesor=profesor)
        elif 'Windows' in user_agent:
            return render_template('templates-pc/rasporeducionica.html', skola=skola, school_id=school_id, data1=data1, data=new_data, isLoggedIn=isLoggedIn, error=error, profesor=profesor)
        else:
            return render_template('templates-pc/rasporeducionica.html', skola=skola, school_id=school_id, data1=data1, data=new_data, isLoggedIn=isLoggedIn, error=error, profesor=profesor)

#dodavanje ili uredivanje rasporeda ucionica popodne
@views.route('/update_table_popodne/', methods=['GET', 'POST'])
def update_table_popodne():
    error=request.args.get("error")
    isLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    user_agent = request.headers.get('User-Agent')
    skola = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
    loggedInProfID = int(decrypt_cookie(request.cookies.get('loggedInProfesorID')))
    profesor = Profesor.query.filter_by(id=loggedInProfID).first()

    if request.method == 'POST':
        data = []
        for i in range(25):
            for j in range(45):
                input_name = "razred1_" + str(i) + "_" + str(j)
                razred_value = request.form.get(input_name)
                if razred_value!=None:
                    data.append(razred_value)
        school_id = request.form['school_id']
        raspored = RasporedUcionicaPopodne.query.filter_by(school_id=school_id).first()

        if raspored:
            existing_raspored_string = raspored.raspored_string
        else:
            existing_raspored_string = ","*1125
        existing_raspored_data = existing_raspored_string.split(',')

        #brisanje djelova starog rasporeda
        new_data = []
        for i in range(len(data)):
            if data[i]=="x" or data[i]=="X":
                new_data.append("")
            elif data[i]!="" and data[i]!=existing_raspored_data[i]:
                new_data.append(data[i])
            else:
                new_data.append(existing_raspored_data[i])

        items_string = ','.join(new_data)
        new_raspored = RasporedUcionicaPopodne(raspored_string=items_string, school_id=school_id)

        existing_raspored = RasporedUcionicaPopodne.query.filter_by(school_id=school_id).first()
        if existing_raspored:
            db.session.delete(existing_raspored)

        db.session.add(new_raspored)
        db.session.commit()

        raspored = RasporedUcionica.query.filter_by(school_id=school_id).first()
        if raspored:
            raspored_string = raspored.raspored_string
        else:
            raspored_string = ","*1125
        data = raspored_string.split(',')



        if 'Mobile' in user_agent:
            return render_template('templates-mobile/rasporeducionica.html', skola=skola, school_id=school_id, data1=new_data, data=data, isLoggedIn=isLoggedIn, error=error, profesor=profesor)
        elif 'Windows' in user_agent:
            return render_template('templates-pc/rasporeducionica.html', skola=skola, school_id=school_id, data1=new_data, data=data, isLoggedIn=isLoggedIn, error=error, profesor=profesor)
        else:
            return render_template('templates-pc/rasporeducionica.html', skola=skola, school_id=school_id, data1=new_data, data=data, isLoggedIn=isLoggedIn, error=error, profesor=profesor)

#prikaz oglasne ploce (obavijesti)
@views.route('/oglasnaploca/', methods=['GET'])
def oglasnaploca():
    error=request.args.get("error")
    user_agent = request.headers.get('User-Agent')
    isLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    skola = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
    isAdminLoggedIn = decrypt_cookie(request.cookies.get('isAdminLoggedIn'))
    profesor=""
    if skola!="True":
        loggedInUserID = int(decrypt_cookie(request.cookies.get('loggedInUser')))
        loggedInUser = User.query.filter_by(id=loggedInUserID).first()
        school_id=loggedInUser.school_id
        sveObavijesti = Obavjesti.query.filter(Obavjesti.school_id == school_id,Obavjesti.date_added >= (datetime.utcnow() - timedelta(days=7))).order_by(Obavjesti.date_added.desc()).all()
    elif skola:
        loggedInProfID = int(decrypt_cookie(request.cookies.get('loggedInProfesorID')))
        profesor = Profesor.query.filter_by(id=loggedInProfID).first()
        loggedInSkolaID = int(decrypt_cookie(request.cookies.get('loggedInSchoolID')))
        sveObavijesti = Obavjesti.query.filter(Obavjesti.school_id == loggedInSkolaID,Obavjesti.date_added >= (datetime.utcnow() - timedelta(days=7))).order_by(Obavjesti.date_added.desc()).all()

    if 'Mobile' in user_agent:
        return render_template('templates-mobile/oglasnaploca.html', admin=isAdminLoggedIn, skola=skola, sve_obavijesti=sveObavijesti, isLoggedIn=isLoggedIn, error=error, profesor=profesor)
    elif 'Windows' in user_agent:
        return render_template('templates-pc/oglasnaploca.html', admin=isAdminLoggedIn, skola=skola, sve_obavijesti=sveObavijesti, isLoggedIn=isLoggedIn, error=error, profesor=profesor)
    else:
        return render_template('templates-pc/oglasnaploca.html', admin=isAdminLoggedIn, skola=skola, sve_obavijesti=sveObavijesti, isLoggedIn=isLoggedIn, error=error, profesor=profesor)


#prikaz rasporeda ucionica
@views.route('/rasporeducionica/', methods=['GET'])
def rasporeducionica():
    error=request.args.get("error")
    user_agent = request.headers.get('User-Agent')
    isUserLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    isSkolaLoggedIn = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
    isAdminLoggedIn = decrypt_cookie(request.cookies.get('isAdminLoggedIn'))
    profesor=""

    if isSkolaLoggedIn!="True":
        loggedInUserID = int(decrypt_cookie(request.cookies.get('loggedInUser')))
        loggedInUser = User.query.filter_by(id=loggedInUserID).first()
        raspored = RasporedUcionica.query.filter_by(school_id=loggedInUser.school_id).first()
        raspored1 = RasporedUcionicaPopodne.query.filter_by(school_id=loggedInUser.school_id).first()
    elif isSkolaLoggedIn:
        loggedInSkolaID = int(decrypt_cookie(request.cookies.get('loggedInSchoolID')))
        raspored = RasporedUcionica.query.filter_by(school_id=loggedInSkolaID).first()
        raspored1 = RasporedUcionicaPopodne.query.filter_by(school_id=loggedInSkolaID).first()
        loggedInProfID = int(decrypt_cookie(request.cookies.get('loggedInProfesorID')))
        profesor = Profesor.query.filter_by(id=loggedInProfID).first()

    if raspored:
        raspored_string = raspored.raspored_string
    else:
        raspored_string = ","*1125
    data = raspored_string.split(',')
    if raspored1:
        raspored_string = raspored1.raspored_string
    else:
        raspored_string = ","*1125
    data1 = raspored_string.split(',')

    if 'Mobile' in user_agent:
        return render_template('templates-mobile/rasporeducionicaprikaz.html', admin=isAdminLoggedIn, skola=isSkolaLoggedIn, data1=data1, data=data, isLoggedIn=isUserLoggedIn, error=error, profesor=profesor)
    elif 'Windows' in user_agent:
        return render_template('templates-pc/rasporeducionicaprikaz.html', admin=isAdminLoggedIn, skola=isSkolaLoggedIn, data1=data1, data=data, isLoggedIn=isUserLoggedIn, error=error, profesor=profesor)
    else:
        return render_template('templates-pc/rasporeducionicaprikaz.html', admin=isAdminLoggedIn, skola=isSkolaLoggedIn, data1=data1, data=data, isLoggedIn=isUserLoggedIn, error=error, profesor=profesor)

#prikaz zamjena za ucenika
@views.route('/prikazzamjenaucenik/', methods=['GET'])
def prikazzamjenaucenik():
    error=request.args.get("error")
    user_agent = request.headers.get('User-Agent')
    isUserLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    isSkolaLoggedIn = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
    isAdminLoggedIn = decrypt_cookie(request.cookies.get('isAdminLoggedIn'))

    loggedInUserID = decrypt_cookie(request.cookies.get('loggedInUser'))
    loggedInUser = User.query.filter_by(id=loggedInUserID).first()

    today = date.today()
    tomarrow = today + timedelta(days=1)
    dayAfterTomarrow = tomarrow + timedelta(days=1)

    zamjeneDanas = Zamjene.query.filter(Zamjene.classroom_id==loggedInUser.classroom_id, Zamjene.datum==today).all()
    zamjeneSutra = Zamjene.query.filter(Zamjene.classroom_id==loggedInUser.classroom_id, Zamjene.datum==tomarrow).all()
    zamjenePrekosutra = Zamjene.query.filter(Zamjene.classroom_id==loggedInUser.classroom_id, Zamjene.datum==dayAfterTomarrow).all()

    daysUntilNextMonday = (-1 - today.weekday()) % 7
    nextMonday = today + timedelta(days=daysUntilNextMonday + 1)
    nextWeekStart = nextMonday
    nextWeekEnd = nextMonday + timedelta(days=6)

    zamjeneSljedeciTjedan = Zamjene.query.filter(Zamjene.datum >= nextWeekStart,Zamjene.datum <= nextWeekEnd, Zamjene.classroom_id==loggedInUser.classroom_id).order_by(Zamjene.datum).all()


    if 'Mobile' in user_agent:
        return render_template('templates-mobile/prikazzamjenaucenik.html', zamjeneDanas=zamjeneDanas, zamjeneSutra=zamjeneSutra, zamjenePrekosutra=zamjenePrekosutra, zamjeneSljedeciTjedan=zamjeneSljedeciTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, error=error)
    elif 'Windows' in user_agent:
        return render_template('templates-pc/prikazzamjenaucenik.html', zamjeneDanas=zamjeneDanas, zamjeneSutra=zamjeneSutra, zamjenePrekosutra=zamjenePrekosutra, zamjeneSljedeciTjedan=zamjeneSljedeciTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, error=error)
    else:
        return render_template('templates-pc/prikazzamjenaucenik.html', zamjeneDanas=zamjeneDanas, zamjeneSutra=zamjeneSutra, zamjenePrekosutra=zamjenePrekosutra, zamjeneSljedeciTjedan=zamjeneSljedeciTjedan, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, error=error)

#prikaz rasporeda sati
@views.route('/prikaziraspored/', methods=['GET'])
def prikaziraspored():
    error=request.args.get("error")
    user_agent = request.headers.get('User-Agent')
    isLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    skola = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
    loggedInUserID = decrypt_cookie(request.cookies.get('loggedInUser'))
    loggedInUser = User.query.filter_by(id=loggedInUserID).first()
    classroom_id = loggedInUser.classroom_id
    raspored_sati = RasporedSati.query.filter_by(classroom_id=classroom_id).first()
    if raspored_sati:
        raspored_string = raspored_sati.raspored_string
    else:
        raspored_string = ","*45
    data = raspored_string.split(',')

    raspored_sati_popodne = RasporedSatiPopodne.query.filter_by(classroom_id=classroom_id).first()
    if raspored_sati_popodne:
        raspored_string = raspored_sati_popodne.raspored_string
    else:
        raspored_string = ","*45
    data1 = raspored_string.split(',')

    if 'Mobile' in user_agent:
        return render_template('templates-mobile/raspored.html', skola=skola, data1=data1, data=data, classroom_id=classroom_id, isLoggedIn=isLoggedIn, error=error)
    elif 'Windows' in user_agent:
        return render_template('templates-pc/raspored.html', skola=skola, data1=data1, data=data, classroom_id=classroom_id, isLoggedIn=isLoggedIn, error=error)
    else:
        return render_template('templates-pc/raspored.html', skola=skola, data1=data1, data=data, classroom_id=classroom_id, isLoggedIn=isLoggedIn, error=error)

#promjena podataka za ucenike
@views.route('/edituserdata', methods=['POST'])
def edituserdata():
    iducenika = request.json.get('iducenika')
    user = User.query.get(iducenika)
    if request.json.get('name') and len(request.json.get('name'))<50:
        namee = request.json.get('name')
    else:
        namee = user.name + " " + user.lastname
    if request.json.get('email') and len(request.json.get('email'))>5 and "@" in request.json.get('email') and "." in request.json.get('email') and len(request.json.get('email'))<50:
        email = request.json.get('email')
    else:
        email = user.email
    if request.json.get('idskole') and len(request.json.get('idskole'))<20:
        if request.json.get('idskole')!="********":
            idskole = request.json.get('idskole')
        else:
            idskole = user.school_id
    if request.json.get('idrazreda') and len(request.json.get('idrazreda'))<20:
        if request.json.get('idrazreda')!="********":
            idrazreda = request.json.get('idrazreda')
        else:
            idrazreda = user.classroom_id


    a = namee.find(' ')
    name=namee[:a]
    lastname=namee[a:]

    if user:
        user.name = name
        user.lastname = lastname
        user.email = email
        user.school_id = idskole
        user.classroom_id = idrazreda

        db.session.commit()

    return "a"

#sustav za zaboravljenu lozinku racuna
@views.route('/forgotpassword', methods=['GET', 'POST'])
def forgotpassword():
    userDevice = request.headers.get('User-Agent')
    #prikaz upitnika za zaboravljenu loznku
    if request.method=="GET":
        if 'Mobile' in userDevice:
            return render_template("templates-mobile/forgotpassword.html")
        elif 'Windows' in userDevice:
            return render_template("templates-pc/forgotpassword.html")
        else:
            return render_template("templates-pc/forgotpassword.html")
    #logika promjene lozinke
    elif request.method=="POST":
        email = request.form["email"]
        randompass = ""
        for i in range(8):
            x=random.randint(48,57)
            y=random.randint(97,122)
            z=random.randint(65,90)
            j=random.randint(1,3)
            if j==1:
                randompass+=chr(x)
            elif j==2:
                randompass+=chr(y)
            elif j==3:
                randompass+=chr(z)

        user = User.query.filter_by(email=email).first()
        if user:
            message = Message(
                subject='Pozdrav od administrativnog tima zamjene.hr',
                recipients=[email],
                body='Tvoja nova lozinka je: ' + randompass + ".")
            mail.send(message)
            user.password = generate_password_hash(randompass, method='pbkdf2:sha256')
            db.session.commit()
        return redirect(url_for("views.login"))

#buducnost..?
@views.route('/notify', methods=['GET', 'POST'])
def notify():
    return render_template("templates-pc/notify.html")

#prikaz za dodavanje predmeta u skoli
@views.route('/dodajpredmet', methods=['GET', 'POST'])
def dodajpredmet():
    error=request.args.get("error")
    isLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    userDevice = request.headers.get('User-Agent')
    isSkolaLoggedIn = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
    schoolID = int(decrypt_cookie(request.cookies.get('loggedInSchoolID')))
    loggedInProfID = int(decrypt_cookie(request.cookies.get('loggedInProfesorID')))
    profesor = Profesor.query.filter_by(id=loggedInProfID).first()
    profesori = Profesor.query.filter_by(school_id=schoolID).order_by(asc(Profesor.name)).all()

    #prikaz stranice
    if request.method=="GET":
        predmeti = Predmeti.query.filter_by(school_id=schoolID).all()
        predmeti = sorted(predmeti, key=lambda x: x.predmet)
        profesori2 = []
        for i in predmeti:
            if Profesor.query.filter_by(id=i.profesor).first():
                profesori2 += [Profesor.query.filter_by(id=i.profesor).first().name]
            else:
                profesori2 += ["Profesor ne postoji!"]

        if 'Mobile' in userDevice:
            return render_template("templates-mobile/dodajpredmet.html", profesori2=profesori2, skola=isSkolaLoggedIn, isLoggedIn=isLoggedIn, school_id=schoolID, predmeti=predmeti, profesor=profesor, profesori=profesori)
        elif 'Windows' in userDevice:
            return render_template("templates-pc/dodajpredmet.html", profesori2=profesori2, skola=isSkolaLoggedIn, isLoggedIn=isLoggedIn, school_id=schoolID, predmeti=predmeti, profesor=profesor, profesori=profesori)
        else:
            return render_template("templates-pc/dodajpredmet.html", profesori2=profesori2, skola=isSkolaLoggedIn, isLoggedIn=isLoggedIn, school_id=schoolID, predmeti=predmeti, profesor=profesor, profesori=profesori)

    #logika dodavanja predmeta
    elif request.method=="POST":
        predmet = request.form['predmet']
        profesor = request.form['profesor']

        novi_predmet = Predmeti(school_id=schoolID, predmet=predmet, profesor=profesor)

        db.session.add(novi_predmet)
        db.session.commit()

        return redirect(url_for("views.dodajpredmet"))

#brisanje predmeta
@views.route('/obrisipredmet', methods=['POST'])
def delete_predmet():
    id_zamjene = request.form['predmet_id']

    predmet = Predmeti.query.get(id_zamjene)

    db.session.delete(predmet)
    db.session.commit()

    return redirect(url_for("views.dodajpredmet", code=303))

#logika dodavanja profesora u databazu
@views.route('/dodajprofesora', methods=['GET', 'POST'])
def dodajprofesora():
        name = request.form.get('name')
        id = random.randrange(1000, 999999)
        pin = random.randrange(1000, 9999)
        if 'is_admin' in request.form:
            is_admin=1
        else:
            is_admin=0
        while Profesor.query.filter_by(id=id).first():
            id = random.randrange(1000, 999999)
        school_id = decrypt_cookie(request.cookies.get('loggedInSchoolID'))
        db.session.add(Profesor(id=id, school_id=school_id, name=name, pin=pin, is_admin=is_admin))
        db.session.commit()
        return redirect(url_for("views.skolaadminmenu"))

#logika brisanja profesora iz databaze
@views.route('/obrisiprofesora', methods=['GET', 'POST'])
def obrisiprofesora():
        id = request.form['id']
        skolaID = request.form['school_id']
        profesor = Profesor.query.get(id)
        sve_zamjene1 = Zamjene.query.filter(Zamjene.school_id==skolaID, Zamjene.stariprofesor==profesor.name).all()
        sve_zamjene2 = Zamjene.query.filter(Zamjene.school_id==skolaID, Zamjene.zamjena.like(f"%{profesor.name}%")).all()
        for i in sve_zamjene1:
            db.session.delete(i)
        for i in sve_zamjene2:
            db.session.delete(i)
        db.session.delete(profesor)
        db.session.commit()
        return redirect(url_for("views.skolaadminmenu"))

#prikaz stranice sa zamjenama za profesore
@views.route('/prikazzamjenaprofesor/', methods=['GET'])
def prikazzamjenaprofesor():
    error=request.args.get("error")
    user_agent = request.headers.get('User-Agent')
    isUserLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    isSkolaLoggedIn = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
    isAdminLoggedIn = decrypt_cookie(request.cookies.get('isAdminLoggedIn'))

    loggedInProfID = int(decrypt_cookie(request.cookies.get('loggedInProfesorID')))
    profesor = Profesor.query.filter_by(id=loggedInProfID).first()
    loggedInProf = Profesor.query.filter_by(id=loggedInProfID).first()


    today = date.today()

    professor_name = loggedInProf.name

    zamjeneDanas = Zamjene.query.filter(Zamjene.zamjena.like(f"%{professor_name}%"), Zamjene.datum==today).all()

    daysUntilNextMonday = (-1 - today.weekday()) % 7
    nextMonday = today + timedelta(days=daysUntilNextMonday + 1)
    nextWeekStart = nextMonday
    nextWeekEnd = nextMonday + timedelta(days=6)
    next3WeeksEnd = nextMonday + timedelta(days=20)

    zamjeneOvajTjedan = Zamjene.query.filter(Zamjene.zamjena.like(f"%{professor_name}%"), Zamjene.datum>=today, Zamjene.datum<nextWeekStart).all()

    zamjeneIducaTriTjedna = Zamjene.query.filter(Zamjene.datum >= nextWeekStart,Zamjene.datum <= next3WeeksEnd, Zamjene.zamjena.like(f"%{professor_name}%")).order_by(Zamjene.datum).all()

    zamjeneUmjestoUlogiranogProfesora = Zamjene.query.filter(Zamjene.datum >= today, Zamjene.datum <= nextWeekEnd, Zamjene.stariprofesor==professor_name).order_by(Zamjene.datum).all()

    if 'Mobile' in user_agent:
        return render_template('templates-mobile/prikazzamjenaprofesor.html', zamjeneOvajTjedan=zamjeneOvajTjedan, zamjeneIducaTriTjedna=zamjeneIducaTriTjedna, zamjeneUmjestoUlogiranogProfesora=zamjeneUmjestoUlogiranogProfesora, zamjeneDanas=zamjeneDanas, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, error=error, profesor=profesor)
    elif 'Windows' in user_agent:
        return render_template('templates-pc/prikazzamjenaprofesor.html', zamjeneOvajTjedan=zamjeneOvajTjedan, zamjeneIducaTriTjedna=zamjeneIducaTriTjedna, zamjeneUmjestoUlogiranogProfesora=zamjeneUmjestoUlogiranogProfesora, zamjeneDanas=zamjeneDanas, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, error=error, profesor=profesor)
    else:
        return render_template('templates-pc/prikazzamjenaprofesor.html', zamjeneOvajTjedan=zamjeneOvajTjedan, zamjeneIducaTriTjedna=zamjeneIducaTriTjedna, zamjeneUmjestoUlogiranogProfesora=zamjeneUmjestoUlogiranogProfesora, zamjeneDanas=zamjeneDanas, admin=isAdminLoggedIn, skola=isSkolaLoggedIn, isLoggedIn=isUserLoggedIn, error=error, profesor=profesor)

#prikaz stranice s povijesti svih zamjena u skoli u zadnjih 60 dana
@views.route('/arhivazamjene', methods=['GET', 'POST'])
def arhivazamjene():
    error=request.args.get("error")
    user_agent = request.headers.get('User-Agent')
    isLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    skola = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
    loggedInSkolaID = int(decrypt_cookie(request.cookies.get('loggedInSchoolID')))
    sve_zamjene = Zamjene.query.filter(Zamjene.school_id == loggedInSkolaID, Zamjene.datum >= (datetime.utcnow() - timedelta(days=60))).order_by(desc(Zamjene.datum)).all()

    if 'Mobile' in user_agent:
        return render_template("templates-mobile/arhivazamjene.html", skola=skola, error=error, isLoggedIn=isLoggedIn, sve_zamjene=sve_zamjene, school_id=loggedInSkolaID)

    elif 'Windows' in user_agent:
        return render_template("templates-pc/arhivazamjene.html", skola=skola, error=error, isLoggedIn=isLoggedIn, sve_zamjene=sve_zamjene, school_id=loggedInSkolaID)

    else:
        return render_template("templates-pc/arhivazamjene.html", skola=skola, error=error, isLoggedIn=isLoggedIn, sve_zamjene=sve_zamjene, school_id=loggedInSkolaID)

#prikaz stranice s povijesti svih obavijesti u skoli
@views.route('/arhivaobavijesti', methods=['GET', 'POST'])
def arhivaobavijesti():
    error=request.args.get("error")
    user_agent = request.headers.get('User-Agent')
    isLoggedIn = decrypt_cookie(request.cookies.get('isUserLoggedIn'))
    skola = decrypt_cookie(request.cookies.get('isSkolaLoggedIn'))
    loggedInSkolaID = int(decrypt_cookie(request.cookies.get('loggedInSchoolID')))
    sve_obavijesti = Obavjesti.query.filter(Obavjesti.school_id == loggedInSkolaID).order_by(Obavjesti.date_added).all()

    if 'Mobile' in user_agent:
        return render_template("templates-mobile/arhivaobavijesti.html", skola=skola, error=error, isLoggedIn=isLoggedIn, sve_obavijesti=sve_obavijesti, school_id=loggedInSkolaID)

    elif 'Windows' in user_agent:
        return render_template("templates-pc/arhivaobavijesti.html", skola=skola, error=error, isLoggedIn=isLoggedIn, sve_obavijesti=sve_obavijesti, school_id=loggedInSkolaID)

    else:
        return render_template("templates-pc/arhivaobavijesti.html", skola=skola, error=error, isLoggedIn=isLoggedIn, sve_obavijesti=sve_obavijesti, school_id=loggedInSkolaID)

#uredivanje imena razreda
@views.route('/editclassroomname', methods=['POST'])
def editclassroomname():
    idRazreda = request.json.get('idRazreda')
    razred = Classroom.query.get(idRazreda)
    if request.json.get('imeRazreda'):
        namee = request.json.get('imeRazreda')
    else:
        namee = razred.name


    if razred:
        razred.name = namee
        db.session.commit()

    return "a"

#logika za uredivanje zamjene
@views.route('/editzamjena', methods=['GET', 'POST'])
def editzamjena():
    if request.method=="POST":
        loggedInSkolaID = int(decrypt_cookie(request.cookies.get('loggedInSchoolID')))
        loggedInProfID = int(decrypt_cookie(request.cookies.get('loggedInProfesorID')))
        #dohvacanje informacija o uredenoj zamjeni
        zamjenaID = request.form['zamjenaID']
        zamjena = Zamjene.query.get(zamjenaID)

        zamjenaza = request.form['zamjenaza']

        datum = request.form['date']
        date_components = datum.split('-')
        datum = '-'.join(date_components[::-1])
        datum = datetime.strptime(datum, '%d-%m-%Y').date()

        od = request.form['from']
        do = ""

        if 'to' in request.form:
            od = od[:2] + ' i ' + str(int(od[0])+1)+ '. sat'

        #slanje obavijesti ucenicima
        classroomID = request.form['razred']
        classroom_name = Classroom.query.filter_by(id=classroomID).first().name

        allUsersOfClassroom = User.query.filter_by(classroom_id=classroomID).all()
        for user in allUsersOfClassroom:
            threading.Thread(target=send_email_in_context, args=(current_app._get_current_object(), user.email, 'Došlo je do promjene u zamjenama', "Imaš novu promjenu za zamjenu. Pogledaj ju na zamjene.hr")).start()



        #slanje obavijestima profesorima kojima je dodan dodatan rad
        broj_novih_predmeta = int(request.form['broj-novih-predmeta-2'])
        novi_predmet_values = [request.form[f'novipredmet{i}'] for i in range(1, broj_novih_predmeta + 1)]
        profesori_za_obavijest=[]
        for i in novi_predmet_values:
            if i!="Slobodan Sat, 0":
                profesor_id_str=i[i.find(",")+3:-2]
                profesori_za_obavijest+=[int(profesor_id_str)]

        #popravak izgleda zbog kasnijeg prikaza korisnicima
        for i in range(len(novi_predmet_values)):
            if novi_predmet_values[i]!="Slobodan Sat, 0":
                novi_predmet_values[i] = novi_predmet_values[i][2:novi_predmet_values[i].find(",")-1]
            else:
                novi_predmet_values[i] = "| Slobodan Sat |"

        #slanje obavijestima profesorima kojima je dodan dodatan rad
        allProfesorsInSchool = Profesor.query.filter_by(school_id=loggedInSkolaID).all()
        for user in allProfesorsInSchool:
            if user.email!="noemail" and user.id in profesori_za_obavijest:
                threading.Thread(target=send_email_in_context, args=(current_app._get_current_object(), user.email, 'Došlo je do promjene u zamjenama', "Dana: " + datum.strftime('%d-%m-%Y') + " ćeš imati " + classroom_name + " " + od + ".")).start()

        novi_predmet_string = ' - '.join(novi_predmet_values)

        biljeska = request.form['biljeska']

        zamjenazaProf = Profesor.query.filter_by(school_id=loggedInSkolaID, name=zamjenaza).first()
        zamjenazaProfStari = Profesor.query.filter_by(school_id=loggedInSkolaID, name=zamjena.stariprofesor).first()
        if zamjenazaProf:
            if zamjenazaProf.email!="noemail" and zamjena.stariprofesor!=zamjenaza:
                threading.Thread(target=send_email_in_context, args=(current_app._get_current_object(), zamjenazaProf.email, 'Nova zamjena na zamjene.hr', "Dana: " + datum.strftime('%d-%m-%Y') + " nećeš imati " + classroom_name + " " + od + ".")).start()
        if zamjenazaProfStari:
            if zamjenazaProfStari.email!="noemail" and zamjena.stariprofesor!=zamjenaza:
                threading.Thread(target=send_email_in_context, args=(current_app._get_current_object(), zamjenazaProfStari.email, 'Nova zamjena na zamjene.hr', "Dana: " + datum.strftime('%d-%m-%Y') + " ćeš ipak imati " + classroom_name + " " + od + ".")).start()

        zamjena.od = od
        zamjena.do = do
        zamjena.datum = datum
        zamjena.zamjena = novi_predmet_string
        zamjena.classroom_id = classroomID
        zamjena.stariprofesor = zamjenaza
        zamjena.school_id = loggedInSkolaID
        zamjena.classroom_name = classroom_name
        zamjena.biljeska = biljeska
        zamjena.dodao_profesor = loggedInProfID

        db.session.commit()

    return redirect(url_for("views.prikazizamjene"))

#logika za skidanje aplikacije za android uredaje
@views.route('/downloadandroid', methods=['POST'])
def download_file():
    return send_file(
        'downloads/zamjene.hr.apk',
        mimetype='application/vnd.android.package-archive',
        download_name='zamjene.hr.apk',
        as_attachment=True
    )

#logika za preuzimanje aplikacije za ios uredanje (potrebno napraviti aplikaciju za ios uredaje)
@views.route('/downloadios', methods=['POST'])
def download_ios_file():
    return send_file(
        'downloads/zamjene.hr.ipa',
        mimetype='application/octet-stream',
        download_name='zamjene.hr.ipa',
        as_attachment=True
    )

#prikaz upitnika za dodavanje e-mail adrese za obavijesti i logika za dodavanje iste u databazu
@views.route('/dodajemailprofesor', methods=['GET','POST'])
def dodajemailprofesor():
    userDevice = request.headers.get('User-Agent')
    loggedInProfID = int(decrypt_cookie(request.cookies.get('loggedInProfesorID')))
    profesor = Profesor.query.filter_by(id=loggedInProfID).first()
    #prikaz upitnika
    if request.method=="GET":
        error=request.args.get("error")
        if 'Mobile' in userDevice:
            return render_template("templates-mobile/dodajemailprofesor.html", error=error)
        elif 'Windows' in userDevice:
            return render_template("templates-pc/dodajemailprofesor.html", error=error)
        else:
            return render_template("templates-pc/dodajemailprofesor.html", error=error)
    #logika dodavanja e-maila
    elif request.method=="POST":
        email = request.form['email']
        if len(email)>5 and "@" in email and "." in email:
            pass
        else:
            error="Nevaljani email."
            return redirect(url_for("views.dodajemailprofesor", error=error))

        profesor.email = email
        db.session.commit()

        return redirect(url_for("views.home"))
    
#prikaz upitnika za uredivanje e-mail adrese za obavijesti i logika za uredivanje iste u databazu
@views.route('/promjeniemailprofesor', methods=['GET','POST'])
def promjeniemailprofesor():
    userDevice = request.headers.get('User-Agent')
    loggedInProfID = int(decrypt_cookie(request.cookies.get('loggedInProfesorID')))
    profesor = Profesor.query.filter_by(id=loggedInProfID).first()
    #prikaz upitnika
    if request.method=="GET":
        error=request.args.get("error")
        if 'Mobile' in userDevice:
            return render_template("templates-mobile/promjeniemailprofesor.html", error=error)
        elif 'Windows' in userDevice:
            return render_template("templates-pc/promjeniemailprofesor.html", error=error)
        else:
            return render_template("templates-pc/promjeniemailprofesor.html", error=error)
    #logika uredivanja e-maila te izmjena istog u databazi
    elif request.method=="POST":
        email = request.form['email']
        if len(email)>5 and "@" in email and "." in email:
            pass
        else:
            error="Nevaljani email."
            return redirect(url_for("views.promjeniemailprofesor", error=error))

        profesor.email = email
        db.session.commit()

        return redirect(url_for("views.home"))

