import json
import os
import psycopg2


def read_config():
    f = open('secrets/config.json')
    return json.load(f)

conf = read_config()

conn = psycopg2.connect(
        host=conf["db"]["server"],
        database=conf["db"]["name"],
        user=conf["db"]["user"],
        password=conf["db"]["pass"])

# Open a cursor to perform database operations
cur = conn.cursor()

# Execute a command: this creates a new table
#cur.execute('DROP TABLE IF EXISTS books;')
#cur.execute('DROP TABLE IF EXISTS info_table;')

cur.execute('DROP TABLE IF EXISTS users;')

cur.execute('CREATE TABLE users (id serial PRIMARY KEY,'
                                 'name varchar (250) NOT NULL,'
                                 'first_name varchar (250) NOT NULL,'
                                 'last_name varchar (250) NOT NULL,'
                                 'email varchar (250) NOT NULL,'
                                 'uuid varchar (100) NOT NULL,'
                                 'date_added date DEFAULT CURRENT_TIMESTAMP);'
                                 )

cur.execute('CREATE TABLE files (id serial PRIMARY KEY,'
                                 'name varchar (250) NOT NULL,'
                                 'uuid varchar (100) NOT NULL,'
                                 'date_added date DEFAULT CURRENT_TIMESTAMP);'
                                 )

# Insert data into the table

cur.execute('INSERT INTO users (name, first_name, last_name, email, uuid) '
            'VALUES (%s, %s, %s, %s, %s)',
            ('Alexander Lachmann',
             'Alexander',
             'Lachmann',
             'alexander.lachmann2@gmail.com',
             'xdsa-sfderw-t5rd-igsd')
            )

cur.execute('INSERT INTO users (name, first_name, last_name, email, uuid) '
            'VALUES (%s, %s, %s, %s, %s)',
            ('Yon Lachmann',
             'Yon',
             'Lachmann',
             'yon@gmail.com',
             '12j2-jkg12v-jssa-lasd')
            )

conn.commit()

cur.close()
conn.close()