from flask import Flask, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager, current_user
from sqlalchemy.exc import IntegrityError, OperationalError
import os
import json
from flask_mail import Mail, Message
import flask_praetorian

from models import db

def create_app():
    app = Flask(__name__)
    

    try:
        app.config.from_object('config.dev')
        db.init_app(app)
    except:
        app.config['ENV'] = os.environ.get("ENV", default="")
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DBURI")
        app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")
        db.init_app(app)

    return app


app = create_app()
app.app_context().push()
jwt = JWTManager(app)
mail = Mail(app)

guard = flask_praetorian.Praetorian()

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(username=identity).one_or_none()

@app.route("/login", methods=["POST"])
def login():
    loginDetails = request.get_json()
    
    if loginDetails:
        if "username" in loginDetails and "password" in loginDetails:
            alreadyExists = User.query.filter_by(username=loginDetails["username"]).first()
            
            if not alreadyExists or not alreadyExists.checkPassword(loginDetails["password"]):
                return json.dumps({"error" : "Wrong username or password entered!"})

            if alreadyExists and alreadyExists.checkPassword(loginDetails["password"]):
                access_token = create_access_token(identity=loginDetails["username"])
                return json.dumps({"access_token" : access_token})

    return json.dumps({"error" : "Invalid login details supplied!"})

@app.route("/register", methods=["POST"])
def register():
    registrationData = request.get_json()

    if registrationData:
        if "username" in registrationData and "password" in registrationData and "confirmPassword" in registrationData:
            filteredUsername = registrationData["username"].replace(" ", "")
            if len(filteredUsername) < 6:
                return json.dumps({"error" : "Username too short!"})
            
            if registrationData["password"] != registrationData["confirmPassword"]:
                return json.dumps({"error" : "Passwords do not match!"})
            
            if len(registrationData["password"]) < 6:
                return json.dumps({"error" : "Password is too short!"})

            try:
                newUser = User(filteredUsername, registrationData["password"])
                db.session.add(newUser)
                db.session.commit()
                return json.dumps({"message" : "Sucesssfully registered!"})
            except IntegrityError:
                db.session.rollback()
                return json.dumps({"error" : "This user already exists!"})
            except OperationalError:
                print("Database not initialized!")
                return json.dumps({"error" : "Database has not been initialized! Please contact the administrator of the application!"})
            except:
                return json.dumps({"error" : "An unknown error has occurred!"})

    return json.dumps({"error" : "Invalid registration details supplied!"})

@app.route("/profile/password", methods=["PUT"])
@jwt_required()
def changePassword():
    newPasswordDetails = request.get_json()

    if newPasswordDetails:
        if "oldPassword" in newPasswordDetails and "password" in newPasswordDetails and "confirmPassword" in newPasswordDetails:
            if not current_user.checkPassword(newPasswordDetails["oldPassword"]):
                return json.dumps({"error" : "The original password you have entered is incorrect!"})

            if newPasswordDetails["password"] != newPasswordDetails["confirmPassword"]:
                return json.dumps({"error" : "Passwords do not match!"})
            
            if len(newPasswordDetails["password"]) < 6:
                return json.dumps({"error" : "Password is too short!"})

            try:
                current_user.setPassword(newPasswordDetails["password"])
                db.session.add(current_user)
                db.session.commit()
                return json.dumps({"message" : "Sucesssfully changed password!"})
            except OperationalError:
                print("Database not initialized!")
                return json.dumps({"error" : "Database has not been initialized! Please contact the administrator of the application!"})
            except:
                return json.dumps({"error" : "An unknown error has occurred!"})

    return json.dumps({"error" : "Invalid password details supplied!"})


@app.route("/identify", methods=["GET"])
@jwt_required()
def identify():
    if current_user:
        return json.dumps({"username" : current_user.username, "universityName" : current_user.enrolledUniversity})
    
    return json.dumps({"error" : "User is not logged in!"})

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('images/favicon.png')

@app.route('/logo.png')
def logo():
    return app.send_static_file('images/logo.png')

@app.route("/", methods=["GET"])
def homepage():
    return app.send_static_file("index.html")


@app.route("/testEmail", methods=["GET"])
def testEmail():
    msg = Message("Hello World!", recipients=["walif98213@threepp.com"], html="Hello World123")
    mail.send(msg)
    return "Message sent!"