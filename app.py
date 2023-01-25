from flask import Flask, jsonify, request
from flask_cors import CORS

from flask_sqlalchemy import SQLAlchemy 
from flask_marshmallow import Marshmallow 

from werkzeug import exceptions
from subprocess import Popen
import pathlib
import hellopy
import boto3

import os
from dotenv import load_dotenv


app = Flask(__name__)


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(dotenv_path='.env', verbose=True)

CORS(app)

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)

#User Class/Model
class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  access_token = db.Column(db.String(100))
  name = db.Column(db.String(100))
  email = db.Column(db.String(100), unique=True)
  guid = db.Column(db.String(100))
  photo = db.Column(db.String(100))
  access_id = db.Column(db.String(100))
  secret_id = db.Column(db.String(100))
  instance_id = db.Column(db.String(100))

  def __init__(self, access_token, name, email, guid, photo, access_id, secret_id, instance_id):
    self.access_token = access_token
    self.name = name
    self.email = email
    self.guid = guid
    self.photo = photo
    self.access_id = access_id
    self.secret_id = secret_id
    self.instance_id = instance_id

# User Schema
class UserSchema(ma.Schema):
  class Meta:
    fields = ('id', 'access_token', 'name', 'email', 'guid', 'photo', 'access_id', 'secret_id', 'instance_id')

# Init schema
user_schema = UserSchema()
users_schema = UserSchema(many=True)

@app.route('/user', methods=['POST'])
def add_User():

    access_token = request.json['data']['accessToken']
    name = request.json['data']['displayName']
    email = request.json['data']['email']
    guid = request.json['data']['guid']
    photo = request.json['data']['photo']

    print(request.json['data'])

    existing_user = User.query.filter_by(guid=guid).first()
    if existing_user:

        print('user alread exists')
        print(existing_user)

        return user_schema.jsonify(existing_user)
    else:
        new_user = User(access_token, name, email, guid, photo, '', '', '')
        #print('new user')
        #print(new_user)

        db.session.add(new_user)
        db.session.commit()
        user_schema.jsonify(new_user)

        return user_schema.jsonify(new_user)


@app.route('/users', methods=['GET'])
def get_user():
  all_users = User.query.all()
  result = users_schema.dump(all_users)
  print('get all users')
  print(result)

  return jsonify(result)


@app.route('/', methods=['GET'])
def home():

    print('request.method')
    print(request.method)
    pathlib.Path(__file__).parent.resolve()
    return jsonify({'message': 'Hello from Flask!'}), 200

admin_aws_access_key_id=os.getenv('admin_aws_access_key_id')
admin_aws_secret_access_key=os.getenv('admin_aws_secret_access_key')

@app.route('/iam/new', methods=['POST'])
def iam_new_user():

    #get guid and start session
    #print(request.json)

    print('user to filter out for IAM Accounts')
    existing_user = User.query.filter_by(guid=request.json['guid']).first()


    #authenticat with admin permissions
    iam = boto3.client('iam',
        aws_access_key_id=admin_aws_access_key_id,
        aws_secret_access_key=admin_aws_secret_access_key,
        region_name='eu-west-2')

        #create user  
    try:
        response = iam.create_user(
        UserName= request.json['name'].replace(" ", "_").lower()
        )

        print(response)

        #save access key of newly created user
        response1 = iam.create_access_key(
            UserName=response['User']['UserName']
        )

        ##save to IAM_user access/secret to database
        #print('after key creation')
        #print(response1)

        AccessKeyId = response1['AccessKey']['AccessKeyId']
        SecretAccessKey = response1['AccessKey']['SecretAccessKey']
        #print('AccessKeyId''AccessKeyId''AccessKeyId')
        #print(AccessKeyId)
        #print(SecretAccessKey)

            #add user to group
        if response['User']['UserId']:
            print(response['User']['UserId'])

            response = iam.add_user_to_group(
                GroupName='student',
                UserName=response['User']['UserName']
            )
            #print('after group creation')
            #print(response)

        existing_user.access_id = AccessKeyId
        existing_user.secret_id = SecretAccessKey
        db.session.commit()

        existing_user_IAM = User.query.filter_by(guid=request.json['guid']).first()

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
    path =  pathlib.Path(__file__).parent.resolve()
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

    existing_user = User.query.filter_by(guid=request.json['guid']).first()
    print('user to filter out for EC2 Views')
    print(existing_user)

    user_data_script = """#!/bin/bash
        echo "Hello World" >> /tmp/data.txt"""      

    try:
        ec2 = boto3.resource('ec2',
            aws_access_key_id=existing_user.access_id,
            aws_secret_access_key=existing_user.secret_id,
            region_name='eu-west-2')

        print(ec2)

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
        print(instance[0].id)
        existing_user.instance_id = instance[0].id
        db.session.commit()

        return jsonify({'message': instance[0].id }), 200

    except Exception as e:
        print('error messag')
        print(str(e))
        return jsonify({'message': str(e)}), 400

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


@app.route('/ec2/instance/terminate', methods=['POST'])
def ec_terminate_instances():

    result = hellopy.hello_world()
    ec2 = boto3.client('ec2',
         aws_access_key_id='AKIAUCXTXAAIXQCVARSC',
         aws_secret_access_key='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',
         region_name='eu-west-2')
         
    response = ec2.terminate_instances(
            InstanceIds=[
            'i-0b26f473cc31c5104',
        ],
    )
    print(response)
    return jsonify({'message': result}), 200



if __name__ == "__main__":
    app.run(debug=True)
