from flask_script import Manager
from main import app
from models import db
import os

manager = Manager(app)

from models import *

@manager.command
def initDB():
    db.create_all(app=app)
    print('Database Initialized!')

@manager.command
def serve():
    print('Application running in ' + app.config['ENV'] + ' mode!')
    app.run(host='0.0.0.0', port = 8080, debug = app.config['ENV'] == 'development')

if __name__ == "__main__":
    manager.run()