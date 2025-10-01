from flask import Flask
import sqlite3

def get_online_friends(user_id):
    online_friends = []
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("Select UserID, Username from Users Where UserId != ? and status='Online' ", (user_id,))
    online_friends = cursor.fetchall()
    db.close()
    return online_friends


