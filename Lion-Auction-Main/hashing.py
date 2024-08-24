from flask import Flask, render_template, request
import sqlite3 as sql
import bcrypt


def userlists():
    allvalue = takeall()
    for i in range(len(allvalue)):
        saltvalue = bcrypt.gensalt()
        encodevalue = allvalue[i][1].encode('UTF-8')
        salt(allvalue[i][0], allvalue[i][1], saltvalue)
        hashed_password = bcrypt.hashpw(encodevalue, saltvalue)
        salted(allvalue[i][0], hashed_password)


def takeall():
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT username ,password FROM users')
    return cursor.fetchall()

def salt (value0, value1, saltvalue):
    connection = sql.connect('database.db')
    connection.execute('UPDATE users SET salt = ? WHERE username = ? AND password = ? ', (saltvalue,value0,value1))
    connection.commit()


#select all value password and salt, update all by using where function
def salted (username,hashed_password):
    connection = sql.connect('database.db')
    connection.execute('UPDATE users SET password = ? WHERE username = ?', (hashed_password, username))
    connection.commit()

userlists()

app = Flask(__name__)
if __name__ == "__main__":
    app.run()