import os
from subprocess import Popen
from dotenv import load_dotenv

from flask import Flask, jsonify, request
from flask_cors import CORS

from functions import add
from routes import main, user, iam, ec2

from werkzeug import exceptions


from db import conn, insert_user, update_user_iam

result = add.add_it(1, 2)
print(result)

app = Flask(__name__)
app.register_blueprint(main.main)
app.register_blueprint(user.users)
app.register_blueprint(iam.iam)
app.register_blueprint(ec2.ec2)

app.app_context().push()
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(dotenv_path='.env', verbose=True)

CORS(app)

cur = conn.cursor()

admin_aws_access_key_id = os.getenv('admin_aws_access_key_id')
admin_aws_secret_access_key = os.getenv('admin_aws_secret_access_key')


if __name__ == "__main__":
    app.run(debug=True)
