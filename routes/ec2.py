import os
from flask import Blueprint, jsonify, request
from db import conn
from models import User
import boto3
from db import conn, insert_user, update_user_iam

admin_aws_access_key_id = os.getenv('admin_aws_access_key_id')
admin_aws_secret_access_key = os.getenv('admin_aws_secret_access_key')

cur = conn.cursor()
User = User.User

ec2 = Blueprint('ec2', __name__)


@ec2.route('/ec2/instances', methods=['GET'])
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


@ec2.route('/ec2/create', methods=['POST'])
def ec2_create():

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


@ec2.route('/ec2/state', methods=['POST'])
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


@ec2.route('/ec2/stop', methods=['POST'])
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


@ec2.route('/ec2/start', methods=['POST'])
def ec_start_instances():

    existing_user = User.query.filter_by(guid=request.json['guid']).first()
    print('user to filter out to stop ec2')
    print(existing_user)

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

    return jsonify({'message': 'ec2 restarted'}), 200


@ec2.route('/ec2/terminate', methods=['POST'])
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
