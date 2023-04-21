from flask import Flask, jsonify, request
from flask_cors import CORS

from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

from werkzeug import exceptions
from subprocess import Popen
import pathlib
import hellopy
import db
import boto3
import json

import os

from json import JSONEncoder
from dotenv import load_dotenv
from db import conn, insert_user


app = Flask(__name__)
app.app_context().push()

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(dotenv_path='.env', verbose=True)

CORS(app)

cur = conn.cursor()

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)

admin_aws_access_key_id = os.getenv('admin_aws_access_key_id')
admin_aws_secret_access_key = os.getenv('admin_aws_secret_access_key')

# User Class/Model


class MyEncoder(JSONEncoder):
    def default(self, obj):
        return obj.__dict__


class Person:
    def __init__(self, name, email, guid, photo, access_id, secret_id):
        self.name = name
        self.email = email
        self.guid = guid
        self.photo = photo
        self.access_id = access_id
        self.secret_id = secret_id

    def __iter__(self):
        yield from {
            "name": self.name,
            "email": self.email,
            "guid": self.guid,
            "photo": self.photo,
            "access_id": self.access_id,
            "secret_id": self.secret_id
        }.items()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String(100))
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    guid = db.Column(db.String(100))
    photo = db.Column(db.String(100))
    access_id = db.Column(db.String(100))
    secret_id = db.Column(db.String(100))
    ec2_instances = db.relationship('Ec2', backref='user')

    def __init__(self, access_token, name, email, guid, photo, access_id, secret_id, ec2_instances):
        self.access_token = access_token
        self.name = name
        self.email = email
        self.guid = guid
        self.photo = photo
        self.access_id = access_id
        self.secret_id = secret_id

    def __repr__(self):
        # rep = {"name": "some_name"}
        rep = f"Hello, {self.name}. your instances are {self.ec2_instances}"
        return rep


class Ec2(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.Text)
    user_id = db.Column(db.String(100), db.ForeignKey('user.email'))

    def __init__(self, instance_id, user_id):
        self.instance_id = instance_id
        self.user_id = user_id

    def __repr__(self):
        return f'{self.instance_id}'


# User Schema
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'access_token', 'name', 'email', 'guid',
                  'photo', 'access_id', 'secret_id', 'ec2_instances')


class Ec2Schema(ma.Schema):
    class Meta:
        fields = ('id', 'instance_id', 'user_id')


# Init schema
user_schema = UserSchema()
users_schema = UserSchema(many=True)

ec2_schema = Ec2Schema()
ec2s_schema = Ec2Schema(many=True)


db.drop_all()
db.create_all()


@app.route('/user', methods=['POST'])
def add_User():

    access_token = request.json['data']['accessToken']
    name = request.json['data']['displayName']
    email = request.json['data']['email']
    guid = request.json['data']['guid']
    photo = request.json['data']['photo']

    cur.execute(f"SELECT * FROM users WHERE email = '{email}';")
    existing_user = cur.fetchone()
    print(email)
    print(existing_user)

    # if some_user exists

    if existing_user == None:
        # if some_user does not exist
        print('user does not exist')
        insert_user(name, email, guid, photo,  '', '')
        cur.execute(f"SELECT * FROM users WHERE email = '{email}';")
        new_user = cur.fetchone()

        print('return newly created')
        print(new_user)

        p1 = Person(new_user[1], new_user[2],
                    new_user[3], new_user[4], '', '')
        print(p1.__dict__)

        return jsonify({'message': p1.__dict__})
    else:
        # if some_user does exist
        print('user does exist')
        p1 = Person(existing_user[1], existing_user[2],
                    existing_user[3], existing_user[4], '', '')
        print(p1.__dict__)
        return jsonify({'message': p1.__dict__})


@app.route('/users', methods=['GET'])
def get_user():
    new_list = []
    cur.execute("SELECT * FROM users;")
    return_data = cur.fetchall()
    print(return_data)

    for i in return_data:
        p1 = Person(i[1], i[2], i[3], i[4], '', '')
        new_list.append(p1.__dict__)

    print(new_list)

    return jsonify({'message': new_list})


@app.route('/', methods=['GET'])
def home():

    print('request.method')
    print(request.method)
    pathlib.Path(__file__).parent.resolve()
    return jsonify({'message': 'Hello from Flask!'}), 200


@app.route('/iam/new', methods=['POST'])
def iam_new_user():

    # get guid and start session
    # print(request.json)

    existing_user = User.query.filter_by(guid=request.json['guid']).first()
    print('user to filter out for IAM Accounts')
    # print(existing_user.access_id)

    # authenticat with admin permissions
    iam = boto3.client('iam',
                       aws_access_key_id=admin_aws_access_key_id,
                       aws_secret_access_key=admin_aws_secret_access_key,
                       region_name='eu-west-2')

    # create user
    try:
        response = iam.create_user(
            UserName=request.json['name'].replace(" ", "_").lower())

        print(response)

        # save access key of newly created user
        response1 = iam.create_access_key(
            UserName=response['User']['UserName']
        )

        # save to IAM_user access/secret to database
        # print('after key creation')
        # print(response1)

        AccessKeyId = response1['AccessKey']['AccessKeyId']
        SecretAccessKey = response1['AccessKey']['SecretAccessKey']
        # print('AccessKeyId''AccessKeyId''AccessKeyId')
        # print(AccessKeyId)
        # print(SecretAccessKey)

        # add user to group
        if response['User']['UserId']:
            print(response['User']['UserId'])

            response = iam.add_user_to_group(
                GroupName='student',
                UserName=response['User']['UserName']
            )
            # print('after group creation')
            # print(response)

        existing_user.access_id = AccessKeyId
        existing_user.secret_id = SecretAccessKey
        db.session.commit()

        existing_user_IAM = User.query.filter_by(
            guid=request.json['guid']).first()

        new_IAM_user = {'accessId': existing_user_IAM.access_id,
                        'secreId': existing_user.secret_id
                        }

        return jsonify({'message': 'user has been succesfully created',
                        'userData': new_IAM_user}), 200

    except Exception as e:
        print('error messag')
        print(str(e))
        return jsonify({'message': str(e)}), 400


@app.route('/bucket', methods=['POST'])
def bucket():

    print('request.method')
    print(request.method)
    path = pathlib.Path(__file__).parent.resolve()
    print(path)
    result = hellopy.hello_world()

    s3 = boto3.resource('s3',
                        aws_access_key_id='AKIAUCXTXAAIXQCVARSC',
                        aws_secret_access_key='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',
                        region_name='eu-west-2'
                        )

    print(s3)

    for bucket in s3.buckets.all():
        print(bucket.name)

    return jsonify({'message': result}), 200


@app.route('/ec2/create', methods=['POST'])
def ec():
    print('user to filter out for EC2 Views')
    existing_user = User.query.filter_by(guid=request.json['guid']).first()

    print(request.json['repo'])

    user_data_script = f"""#!/bin/bash
        # Enable logs
        exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

        # Install Git
        echo "Installing Git"
        yum update -y
        yum install git -y

        # Install NodeJS
        echo "Installing NodeJS"
        yum install -y gcc-c++ make
        curl -sL https://rpm.nodesource.com/setup_16.x | sudo -E bash -
        yum install -y nodejs

        # Clone website code
        echo "Cloning website"
        mkdir -p /demo-website
        cd /demo-website
        git clone {request.json['repo']} .

        # Install dependencies
        echo "Installing dependencies"
        npm install

        # Forward port 80 traffic to port 4000
        echo "Forwarding 80 -> 4000"
        iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 4000
        # iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 4000

        # Install & use pm2 to run Node app in background
        echo "Installing & starting pm2"
        npm install pm2@latest -g
        pm2 start app.js
        """

    try:
        ec2 = boto3.resource('ec2',
                             aws_access_key_id=existing_user.access_id,
                             aws_secret_access_key=existing_user.secret_id,
                             region_name='eu-west-2')

        instance = ec2.create_instances(
            ImageId="ami-084e8c05825742534",
            MinCount=1,
            MaxCount=1,
            InstanceType="t2.micro",
            KeyName="KeyPair1",
            SecurityGroupIds=[
                    'sg-0f6e6789ff4e7e7c1',
            ],
            UserData=user_data_script
        )

        print('successfully lauched an instance save it to User db')
        print(instance)
        print(f"{instance[0].id}")

        ec2 = Ec2(instance_id=str(instance[0].id), user_id=existing_user.email)
        db.session.add(ec2)
        db.session.commit()

        print('pritn ec2')
        print(ec2)
        print(existing_user.ec2_instances)
        return jsonify({'message': "ec2"}), 200

    except Exception as e:
        print('error messag')
        print(str(e))
        return jsonify({'message': str(e)}), 400


@app.route('/ec2/state', methods=['POST'])
def ec_view_ec2state():

    existing_user = User.query.filter_by(guid=request.json['guid']).first()
    print('user to filter out for EC2 Views')
    print(existing_user)

    EC2_CLIENT = boto3.client('ec2',
                              aws_access_key_id=existing_user.access_id,
                              aws_secret_access_key=existing_user.secret_id,
                              region_name='eu-west-2')

    response = EC2_CLIENT.describe_instances(
        InstanceIds=[
            existing_user.instance_id
        ])

    print(response)

    return jsonify({'message': response}), 200


@app.route('/ec2/instances', methods=['POST'])
def ec_view_instances():
    instance_list = []

    existing_user = User.query.filter_by(guid=request.json['guid']).first()
    print('user to filter out for EC2 Views')
    print(existing_user)

    ec2 = boto3.resource('ec2',
                         aws_access_key_id=existing_user.access_id,
                         aws_secret_access_key=existing_user.secret_id,
                         region_name='eu-west-2')

    for instance in ec2.instances.all():
        instance_list.append(instance.id)
        print(instance.id)

    print(instance_list)

    return jsonify({'message': instance_list}), 200


@app.route('/ec2/stop', methods=['POST'])
def ec_stop_instances():

    existing_user = User.query.filter_by(guid=request.json['guid']).first()
    print('user to filter out to stop ec2')
    print(existing_user)

    result = hellopy.hello_world()
    ec2 = boto3.client('ec2',

                       aws_access_key_id=existing_user.access_id,
                       aws_secret_access_key=existing_user.secret_id,

                       region_name='eu-west-2')

    response = ec2.stop_instances(
        InstanceIds=[
            existing_user.instance_id,
        ],
        Hibernate=False,
        DryRun=False,
        Force=False
    )

    print(response)

    return jsonify({'message': result}), 200


@app.route('/ec2/start', methods=['POST'])
def ec_start_instances():

    existing_user = User.query.filter_by(guid=request.json['guid']).first()
    print('user to filter out to stop ec2')
    print(existing_user)

    result = hellopy.hello_world()
    ec2 = boto3.client('ec2',
                       aws_access_key_id=existing_user.access_id,
                       aws_secret_access_key=existing_user.secret_id,
                       region_name='eu-west-2')

    response = ec2.start_instances(
        InstanceIds=[
            existing_user.instance_id,
        ],
        AdditionalInfo='string',
        DryRun=False
    )

    print(response)

    return jsonify({'message': result}), 200


@app.route('/ec2/terminate', methods=['POST'])
def ec_terminate_instances():

    existing_user = User.query.filter_by(guid=request.json['guid']).first()
    ec2 = boto3.client('ec2',
                       aws_access_key_id=existing_user.access_id,
                       aws_secret_access_key=existing_user.secret_id,
                       region_name='eu-west-2')

    response = ec2.terminate_instances(
        InstanceIds=[
            existing_user.instance_id,
        ],
    )

    print(response)
    return jsonify({'message': 'EC2 Terminated'}), 200


if __name__ == "__main__":
    app.run(debug=True)
