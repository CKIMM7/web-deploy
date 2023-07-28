from flask import Blueprint, jsonify, request
from db import conn

cur = conn.cursor()


class Person:
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


users = Blueprint('users', __name__)


@users.route('/users')
def index():
    new_list = []
    cur.execute("SELECT * FROM users;")
    return_data = cur.fetchall()
    print(return_data)

    for i in return_data:
        p1 = Person(i[0], i[1], i[2], i[3], i[4], i[5], i[6])
        new_list.append(p1.__dict__)

    print(new_list)

    return jsonify({'users': new_list})


# @app.route('/users', methods=['GET'])
# def get_user():
#     new_list = []
#     cur.execute("SELECT * FROM users;")
#     return_data = cur.fetchall()
#     print(return_data)

#     for i in return_data:
#         p1 = Person(i[0], i[1], i[2], i[3], i[4], i[5], i[6])
#         new_list.append(p1.__dict__)

#     print(new_list)

#     return jsonify({'users': new_list})
