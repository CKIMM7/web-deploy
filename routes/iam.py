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

iam = Blueprint('iam', __name__)


@iam.route('/iam/new', methods=['POST'])
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
