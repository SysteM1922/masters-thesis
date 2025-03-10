import string
from flask import Flask, render_template,request
from flask_socketio import SocketIO,join_room, leave_room, emit
from flask_cors import CORS
import eventlet
import eventlet.wsgi
import requests
import time
import math
import random

app = Flask(__name__)
socketio = SocketIO(app,cors_allowed_origins='*')

users = {}  #{id: (idsocket, addr, {onlinefriends})}
rooms = {}  #{room: [users]}

##Cuidado com os ips nas funcs de chamada ao server homegym


print("Server is running")

@socketio.on('connect')
def connect():                    
    print('Client connected')
    

@socketio.on('handle_connect')
def handle_connect(data):
    onlinefriends = {}
    user_id_socket = request.sid
    user_addr = request.remote_addr
    userID = data['id']
    onlinefriends = get_online_friends(userID)       
    users[userID] = (user_id_socket, user_addr,onlinefriends)

    #refresh online friends-- percorrer o dicionario e pesquisar os amigos online de todos os users ligados e dar update
    for id, user in users.items():
        if id != userID:
            onlinefriends_2 = get_online_friends(id)
            users[id] = (user[0], user[1], onlinefriends_2)

    #check if user was in any room and rejoin
    username = get_username(userID)
    for room in rooms:
        if username in rooms[room]:
            join_room(room)
                     
    print(users)


@socketio.on('disconnect')
def disconnect():
    for id, user in users.items():
        if user[0] == request.sid:
            print('User disconnected: ', id)
            username = get_username(id)
            del users[id]
            break
    for id, user in users.items():
        time.sleep(1.5)
        onlinefriends = get_online_friends(id)
        users[id] = (user[0], user[1], onlinefriends)
    


    print(users)
    print(rooms)



@socketio.on('leave')
def handle_leave(data):
    room = data['room']
    leave_room(room)
    emit('receive_message', {'text': 'User has left the room'}, room=room)
    

@socketio.on('send_invite')
def send_invite(data):
    room = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    friend_name = data['friend_name']
    username = get_username(data['userID'])
    message = data['message']

    #check if user who sent the invite is already in a room
    if len(rooms) > 0:
        for r in rooms:
            if username in rooms[r]:
                for user_id, user_info in users.items():
                    if user_info[0] == request.sid:
                        online_friends = user_info[2]
                        for friend_id, friend_username in online_friends.items():
                            if friend_name == friend_username:
                                friend_id = int(friend_id)
                                friend_socket = users[friend_id][0]
                                print('Invite sent to: ', friend_username, ' with socket: ', friend_socket)
                                emit('receive_invite', {'message': message, 'room': r, 'friend_name': friend_username}, to=friend_socket)
                                return
            
    if room not in rooms:
        join_room(room)
        print('socket: ', request.sid , ' joined room: ', room)
        rooms[room] = [username]
    
    

    for user_id, user_info in users.items():
        if user_info[0] == request.sid:
            online_friends = user_info[2]
            for friend_id, friend_username in online_friends.items():
                if friend_name == friend_username:
                    friend_id = int(friend_id)
                    friend_socket = users[friend_id][0]
                    print('Invite sent to: ', friend_username, ' with socket: ', friend_socket)
                    emit('receive_invite', {'message': message, 'room': room, 'friend_name': friend_username}, to=friend_socket)
                    return
            

@socketio.on('handle_invite')
def handle_invite(data):
    print('Invite received')

    room = data['room']
    friend_name = data['friend_name']

    if room not in rooms:
        return
    
    #check if user already in a room                     
    for r in rooms:
        if friend_name in rooms[r]:
            return
    
    join_room(room)
    rooms[room].append(friend_name)

    print('socket: ', request.sid , ' joined room: ', room)
    emit('receive_message', {'message': 'User has joined the room', 'friend_name': friend_name}, to=room)

    print('All rooms: ', rooms)



@socketio.on('send_message')
def send_message(data):
    for user_id, user_info in users.items():
        if user_info[0] == request.sid:
            id = user_id

    username = get_username(id)

    for room in rooms:
        if username in rooms[room]:
            message = data['message']
            if message == 'start_session':
                emit('receive_message', {'message': message,'room':room}, room=room)
            elif message == 'finish_plan':
                emit('receive_message', {'message': message}, room=room)
                del rooms[room]
                print('All rooms: ', rooms)
                return
            else:
                emit('receive_message', {'message': message}, room=room)
    



#--------------------------------funcs http request ao server homegym----------------------------------
def get_online_friends(userID):
    response = requests.get("https://192.168.1.70:5000/getOnlineFriends/"+str(userID), verify= False) #certificado n esta a funcionar 

    if response != []:
        return response.json()
    else:   
        return None
    
def get_username(id):
    response = requests.get("https://192.168.1.70:5000/getUsername/"+str(id), verify= False)

    if response != []:
        return response.json()
    else:
        return None
    


if __name__ == '__main__':
    socketio.run(app,host='0.0.0.0', port="5004", keyfile='key.pem', certfile='cert.pem')
    
   


