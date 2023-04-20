import psycopg2

conn = psycopg2.connect(
    database="testdb",
    user="postgres",
    password="postgres",
    host="database-1.c4rcnm5z6bgf.eu-west-2.rds.amazonaws.com",
    port='5432'
)

cur = conn.cursor()
cur.execute("DROP TABLE users;")

cur.execute("CREATE TABLE users (id serial PRIMARY KEY, name VARCHAR ( 50 ) UNIQUE NOT NULL, email VARCHAR ( 50 ) UNIQUE NOT NULL, guid VARCHAR ( 50 ) UNIQUE NOT NULL, photo VARCHAR ( 100 ) UNIQUE NOT NULL, access_id VARCHAR ( 50 ), secret_id VARCHAR ( 50 ));")

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
