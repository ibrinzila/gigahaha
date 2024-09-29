import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from models import User, ChatLog, Feedback

with app.app_context():
    db.create_all()

from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
