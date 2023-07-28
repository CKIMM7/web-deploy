import os
from subprocess import Popen
from dotenv import load_dotenv

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug import exceptions

from routes import main, user, iam, ec2, beanstalk
from functions import add


app = Flask(__name__)
app.register_blueprint(main.main)
app.register_blueprint(user.users)
app.register_blueprint(iam.iam)
app.register_blueprint(ec2.ec2)

CORS(app)

if __name__ == "__main__":
    app.run(debug=True)
