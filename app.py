from flask import *
import pymongo
from flask_session import Session
import random
import smtplib
from email.message import EmailMessage
import datetime
import re
import base64
from validate_email import validate_email
from dotenv import load_dotenv
import os
import bcrypt

load_dotenv()

def generate_otp(user_email):
    new_otp = random.randint(100000, 999999)
    sender_email = os.getenv("email_id")
    sender_password = os.getenv("email_password")
    receiver_email = user_email
    message_text = f"The OTP is {new_otp}"
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    if validate_email(receiver_email):
        server.sendmail(sender_email, receiver_email, message_text)
        return new_otp
    else:
        return 0


def add_user(first_name, last_name, email, phone, password, gender):
    users_column.insert_one({"First_Name":first_name, "Last_Name":last_name, "Email":email , "Phone":phone , "Password":password, "Gender":gender, "Role":'user'})


project_server = pymongo.MongoClient(os.getenv("pymongo_client"))
db_column = project_server['selyer']
users_column = db_column['users']

app = Flask(__name__)
app.config['SESSION_TYPE'] = os.getenv("session_type")
app.config['SECRET_KEY'] = os.getenv("secret_key")
sess = Session()

@app.route('/',methods=['GET','POST'])
def home():
    session['name'] = None
    return render_template('home.html')

@app.route('/login',methods=['GET','POST'])
def login():
    msg = ""
    if request.method == 'POST':
        details = request.form
        name = details['username']
        password = details['password']
        user = users_column.find_one({"$or":[{'Email':name},{'Phone':name}]})
        if bcrypt.checkpw(password.encode('utf-8'), user['Password']):
            session['name'] = user['First_Name']
            session['role'] = user['Role']
            session['email'] = user['Email']
            session['phone'] = user['Phone']
            return redirect('/dashboard')
        else:
            msg = "wrong Username/Password"
    return render_template('login.html',msg=msg)

@app.route('/signup',methods=['GET','POST'])
def signup():
    msg = ""
    if request.method == 'POST':
        details = request.form
        first_name = details['first_name']
        last_name = details['last_name']
        email = details['email_address']
        phone = details['phone']
        password = details['password']
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        gender = details['gender']
        otp=  details['otp']
        if int(otp)==session['new_otp']  :
            b= add_user(first_name, last_name, email, phone, password_hash, gender)
            return redirect('/login')
        else:
            msg = "Wrong Otp"
    return render_template('signup.html',msg= msg)

@app.route('/generate_otp_email',methods=['GET','POST'])
def generate_otp_email():
    if request.method == 'POST':
        email=request.form.get('data')
        email_otp = generate_otp(email)
        session['new_otp'] = email_otp
        if email_otp == 0:
            otp_status = 1
        else :
            otp_status = email_otp
    return jsonify ({'success':True,'otp':otp_status})

@app.route('/forgot_password',methods=['GET','POST'])
def forgot_password():
    msg=" "
    if request.method == 'POST':
        email=request.form['email']
        user = users_column.find_one({'Email':email})
        if user:
            email_otp = generate_otp(email)
            session['forgot_password_email'] = email
            session['forgot_password_otp'] = email_otp
            return redirect('/forgot_password_otp')
        else :
            msg="The Email Dont Exist"
    return render_template('forgot_password.html', msg=msg)

@app.route('/forgot_password_otp',methods=['GET','POST'])
def forgot_password_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        email_otp = session['forgot_password_otp']
        if int(entered_otp) == email_otp:
            return redirect('/reset_password')
    return render_template('forgot_password_otp.html')

@app.route('/reset_password',methods=['GET','POST'])
def reset_password():
    msg = " "
    if request.method == 'POST':
        new_password = request.form['new_password']
        reenter_password = request.form['reenter_password']
        if new_password == reenter_password:
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            users_column.update_one({'Email':session['forgot_password_email']}, { "$set": { "Password": password_hash } })
            return redirect('/login')
        else:
            msg = "Passwords didn't match"
    return render_template('reset_password.html',msg=msg)

@app.route("/dashboard",methods=['GET','POST'])
def dashboard():
    return render_template('dashboard.html')

if __name__=='__main__':
    app.run(debug=True)