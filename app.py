from flask import Flask, jsonify, request
from functions import add
from routes import main, user

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
from db import conn, insert_user, update_user_iam

result = add.add_it(1, 2)
print(result)

app = Flask(__name__)
app.app_context().push()
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(dotenv_path='.env', verbose=True)

CORS(app)

cur = conn.cursor()

admin_aws_access_key_id = os.getenv('admin_aws_access_key_id')
admin_aws_secret_access_key = os.getenv('admin_aws_secret_access_key')

# User Class/Model


class MyEncoder(JSONEncoder):
    def default(self, obj):
        return obj.__dict__


class User:
    def __init__(self, id, name, email, guid, photo, access_id, secret_id):
        self.id = id
        self.name = name
        self.email = email
        self.guid = guid
        self.photo = photo
        self.access_id = access_id
        self.secret_id = secret_id

    def __iter__(self):
        yield from {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "guid": self.guid,
            "photo": self.photo,
            "access_id": self.access_id,
            "secret_id": self.secret_id
        }.items()


app.register_blueprint(main.main)
app.register_blueprint(user.users)


@app.route('/iam/new', methods=['POST'])
def iam_new_user():

    guid = request.json['guid']
    cur.execute(f"SELECT * FROM users WHERE user_name = '{guid}';")
    existing_user = cur.fetchone()
    print(existing_user)

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

        update_user_iam(AccessKeyId, SecretAccessKey, guid)
        cur.execute(f"SELECT * FROM users WHERE user_guid = '{guid}';")
        existing_user = cur.fetchone()
        print('existing_user after update')
        p1 = User(existing_user[0], existing_user[1], existing_user[2],
                  existing_user[3], existing_user[4], existing_user[5], existing_user[6])
        print(p1.__dict__)
        return jsonify({'user': p1.__dict__}), 200

    except Exception as e:
        print('error messag')
        print(str(e))
        return jsonify({'message': str(e)}), 400


@app.route('/iam/delete_key', methods=['POST'])
def iam_delete_access_key():
    print('/iam/delete_key')

    guid = request.json['guid']
    print(guid)
    cur.execute(f"SELECT * FROM users WHERE user_guid = '{guid}';")
    existing_user = cur.fetchone()

    print(existing_user[1].replace(" ", "_").lower())

    # authenticat with admin permissions
    iam = boto3.client('iam',
                       aws_access_key_id=admin_aws_access_key_id,
                       aws_secret_access_key=admin_aws_secret_access_key,
                       region_name='eu-west-2')

    try:
        access_key_response = iam.delete_access_key(
            UserName=existing_user[1].replace(" ", "_").lower(),
            AccessKeyId=existing_user[5])
        print(access_key_response)

        if access_key_response:

            remove_user_from_group_response = iam.remove_user_from_group(
                GroupName='student',
                UserName=existing_user[1].replace(" ", "_").lower()
            )
            print(remove_user_from_group_response)

            if remove_user_from_group_response:
                delete_user_response = iam.delete_user(
                    UserName=existing_user[1].replace(" ", "_").lower()
                )
                print(delete_user_response)
                cur.execute(
                    f"DELETE FROM users WHERE user_guid = '{guid}';")
                conn.commit()

                cur.execute("""SELECT * FROM users;""")
                fetch_users = cur.fetchall()
                print(fetch_users)

            return jsonify({'message': 'user successfully deleted'}), 200

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

    guid = request.json['guid']
    cur.execute(
        f"SELECT * FROM users WHERE user_guid = '{guid}';")
    user_aws_credentials = cur.fetchone()
    print('fetch all user credentials')
    print(user_aws_credentials)
    print(user_aws_credentials[5])
    print(user_aws_credentials[6])

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
                             aws_access_key_id=user_aws_credentials[5],
                             aws_secret_access_key=user_aws_credentials[6],
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

        cur.execute("INSERT INTO ec2s (user_id, ec2_name) VALUES (%s, %s)",
                    (user_aws_credentials[0], f"{instance[0].id}"))
        conn.commit()

        cur.execute(
            """SELECT users.user_id, users.user_name, ec2_name FROM users INNER JOIN ec2s ON ec2s.user_id = users.user_id WHERE users.user_email = 'dyounggkim@gmail.com';""")
        join_sql_kim = cur.fetchall()
        print(join_sql_kim)

        return jsonify({'message': "ec2"}), 200

    except Exception as e:
        print('error messag')
        print(str(e))
        return jsonify({'message': str(e)}), 400


@app.route('/ec2/instances', methods=['POST'])
def ec_view_instances():

    instance_list = []

    guid = request.json['guid']
    cur.execute(
        f"SELECT * FROM users WHERE user_guid = '{guid}';")
    user_aws_credentials = cur.fetchone()
    print('fetch all user credentials')
    print(user_aws_credentials)
    print(user_aws_credentials[5])
    print(user_aws_credentials[6])

    ec2 = boto3.resource('ec2',
                         aws_access_key_id=user_aws_credentials[5],
                         aws_secret_access_key=user_aws_credentials[6],
                         region_name='eu-west-2')

    for instance in ec2.instances.all():
        instance_list.append(instance.id)
        print(instance.id)

    print(instance_list)

    return jsonify({'message': instance_list}), 200


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
