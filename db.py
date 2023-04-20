import psycopg2
import os

aws_db_database = os.getenv('aws_db_database')
aws_db_user = os.getenv('aws_db_user')
aws_db_password = os.getenv('aws_db_password')
aws_db_host = os.getenv('aws_db_host')


conn = psycopg2.connect(
    database=aws_db_database,
    user=aws_db_user,
    password=aws_db_password,
    host=aws_db_host,
    port='5432'
)

cur = conn.cursor()
try:
    cur.execute("DROP TABLE users;")
except psycopg2.Error as e:
    print(e.pgcode)

try:
    cur.execute("CREATE TABLE users (id serial PRIMARY KEY, name VARCHAR ( 50 ) UNIQUE NOT NULL, email VARCHAR ( 50 ) UNIQUE NOT NULL, guid VARCHAR ( 50 ) UNIQUE NOT NULL, photo VARCHAR ( 100 ) UNIQUE NOT NULL, access_id VARCHAR ( 50 ), secret_id VARCHAR ( 50 ));")
except psycopg2.Error as e:
    print(e.pgcode)

cur.execute("INSERT INTO users (name, email, guid, photo, access_id, secret_id) VALUES (%s, %s, %s, %s, %s, %s)",
            ('kim1', 'kim@gmail.com', 'guid', 'photo', '', ''))

cur.execute("INSERT INTO users (name, email, guid, photo, access_id, secret_id) VALUES (%s, %s, %s, %s, %s, %s)",
            ('eve', 'eve@gmail.com', 'guid1', 'photo1', '', ''))


def insert_user(name, email, guid, photo, access_id, secret_id):
    cur.execute("INSERT INTO users (name, email, guid, photo, access_id, secret_id) VALUES (%s, %s, %s, %s, %s, %s)",
                (name, email, guid, photo, '', ''))
    conn.commit()


conn.commit()
cur.execute("SELECT * FROM users;")
return_data = cur.fetchall()
print(return_data)
