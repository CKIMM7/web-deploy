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
    # cur.execute("DROP TABLE users;")
    # cur.execute("DROP TABLE IF EXISTS contacts;")

    cur.execute("DROP TABLE IF EXISTS ec2s;")
    cur.execute("DROP TABLE IF EXISTS users;")
    cur.execute("DROP TABLE IF EXISTS users;")
    conn.commit()
    print('drop executed')
except psycopg2.Error as e:
    print(e)

try:

    # cur.execute("CREATE TABLE users (id serial PRIMARY KEY, name VARCHAR ( 50 ) UNIQUE NOT NULL, email VARCHAR ( 50 ) UNIQUE NOT NULL, guid VARCHAR ( 50 ) UNIQUE NOT NULL, photo VARCHAR ( 100 ) UNIQUE NOT NULL, access_id VARCHAR ( 50 ), secret_id VARCHAR ( 50 ));")

    sql_create_users = """CREATE TABLE users(
   user_id INT GENERATED ALWAYS AS IDENTITY,
   user_name VARCHAR(255) NOT NULL,
   user_email VARCHAR(255) NOT NULL,
   user_guid VARCHAR(255) NOT NULL,
   user_photo VARCHAR(255) NOT NULL,
   access_id VARCHAR(255),
   secret_id VARCHAR(255),
   PRIMARY KEY(user_id));"""

    sql_create_ec2s = """CREATE TABLE ec2s(
   ec2_id INT GENERATED ALWAYS AS IDENTITY,
   user_id INT,
   ec2_name VARCHAR(255) NOT NULL,
   PRIMARY KEY(ec2_id),
   CONSTRAINT fk_user
      FOREIGN KEY(user_id) 
	  REFERENCES users(user_id)
      ON DELETE CASCADE
    );"""

    cur.execute(sql_create_users)
    cur.execute(sql_create_ec2s)
    conn.commit()

except psycopg2.Error as e:
    print(e)

cur.execute("INSERT INTO users (user_name, user_email, user_guid, user_photo, access_id, secret_id) VALUES (%s, %s, %s, %s, %s, %s)",
            ('kim', 'kim@gmail.com', 'guid', 'photo_kim', '', ''))

cur.execute("INSERT INTO users (user_name, user_email, user_guid, user_photo, access_id, secret_id) VALUES (%s, %s, %s, %s, %s, %s)",
            ('eve', 'eve@gmail.com', 'guid1', 'photo_eve', '', ''))

cur.execute("INSERT INTO ec2s (user_id, ec2_name) VALUES (%s, %s)",
            (1, 'some_ec2_name_1'))

cur.execute("INSERT INTO ec2s (user_id, ec2_name) VALUES (%s, %s)",
            (1, 'some_ec2_name_2'))

cur.execute("INSERT INTO ec2s (user_id, ec2_name) VALUES (%s, %s)",
            (2, 'some_ec2_name_3'))

cur.execute("INSERT INTO ec2s (user_id, ec2_name) VALUES (%s, %s)",
            (2, 'some_ec2_name_4'))

conn.commit()

# cur.execute("SELECT * FROM test;")

cur.execute(
    """SELECT * FROM users;""")
fetch_users = cur.fetchall()
print(fetch_users)


cur.execute(
    """SELECT users.user_id, users.user_name, ec2_name 
    FROM users 
    INNER JOIN ec2s
    ON ec2s.user_id = users.user_id WHERE users.user_name = 'kim';""")

join_sql_kim = cur.fetchall()
print(join_sql_kim)

cur.execute(
    """SELECT users.user_id, users.user_name, ec2_name 
    FROM users 
    INNER JOIN ec2s
    ON ec2s.user_id = users.user_id WHERE users.user_name = 'eve';""")

join_sql_eve = cur.fetchall()
print(join_sql_eve)


cur.execute(
    """SELECT users.user_id, users.user_name, ec2_name 
    FROM ec2s
    INNER JOIN users
    ON users.user_id = ec2s.user_id WHERE ec2s.ec2_name = 'some_ec2_name_2';""")

join_ec2s = cur.fetchall()
print(join_ec2s)


# cur.execute("INSERT INTO users (name, email, guid, photo, access_id, secret_id) VALUES (%s, %s, %s, %s, %s, %s)",
#             ('kim1', 'kim@gmail.com', 'guid', 'photo', '', ''))

# cur.execute("INSERT INTO users (name, email, guid, photo, access_id, secret_id) VALUES (%s, %s, %s, %s, %s, %s)",
#             ('eve', 'eve@gmail.com', 'guid1', 'photo1', '', ''))


def insert_user(name, email, guid, photo, access_id, secret_id):

    cur.execute("INSERT INTO users (user_name, user_email, user_guid, user_photo, access_id, secret_id) VALUES (%s, %s, %s, %s, %s, %s)",
                (name, email, guid, photo, '', ''))
    conn.commit()


def update_user_iam(access_id, secret_id, guid):
    sql = """ UPDATE users SET access_id = %s, secret_id = %s WHERE user_guid = %s"""
    cur.execute(sql, (access_id, secret_id, guid))
    conn.commit()


# conn.commit()
# cur.execute("SELECT * FROM users;")
# return_data = cur.fetchall()
# print(return_data)
