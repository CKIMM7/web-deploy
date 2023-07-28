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

users = Blueprint('users', __name__)
# user = Blueprint('user', __name__)


@users.route('/users', methods=['GET'])
def list_users():
    new_list = []
    cur.execute("SELECT * FROM users;")
    return_data = cur.fetchall()
    print(return_data)

    for i in return_data:
        p1 = User(i[0], i[1], i[2], i[3], i[4], i[5], i[6])
        new_list.append(p1.__dict__)

    print(new_list)

    return jsonify({'users': new_list})


@users.route('/user', methods=['POST'])
def add_User():
    print('/user post')

    access_token = request.json['data']['accessToken']
    name = request.json['data']['displayName']
    email = request.json['data']['email']
    guid = request.json['data']['guid']
    photo = request.json['data']['photo']

    # look into iam not my own database

    cur.execute(f"SELECT * FROM users WHERE user_email = '{email}';")
    existing_user = cur.fetchone()
    print(existing_user)

    if existing_user == None:
        # if some_user does not exist
        print('user does not exist, creating user')
        insert_user(name, email, guid, photo,  '', '')
        cur.execute(
            f"SELECT * FROM users WHERE user_email = '{email}';")
        new_user = cur.fetchone()

        print('return newly created')
        print(new_user)

        p1 = User(new_user[0], new_user[1], new_user[2],
                  new_user[3], new_user[4], new_user[5], new_user[6])
        print(p1.__dict__)

        return jsonify({'user': p1.__dict__, 'status': 'new user'})
    else:
        # if some_user does exist
        print('user does exist')

        iam = boto3.client('iam',
                           aws_access_key_id=admin_aws_access_key_id,
                           aws_secret_access_key=admin_aws_secret_access_key,
                           region_name='eu-west-2')

        # response = iam.get_user(
        #     UserName='Dong_Young_Kim')

        # print(response)

        p1 = User(existing_user[0], existing_user[1], existing_user[2],
                  existing_user[3], existing_user[4], existing_user[5], existing_user[6])
        print(p1.__dict__)
        return jsonify({'user': p1.__dict__, 'status': 'existing user'})
