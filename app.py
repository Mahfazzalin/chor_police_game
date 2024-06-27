from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

players = {}
rooms = {}
room_count = 0

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create_room')
def create_room(data):
    global room_count
    room_count += 1
    room_key = f"room{room_count}"
    rooms[room_key] = [data['username']]
    join_room(room_key)
    players[data['username']] = {'room': room_key, 'points': 0}
    emit('room_created', {'room_key': room_key, 'username': data['username']})

@socketio.on('join_room')
def join(data):
    room_key = data['room_key']
    username = data['username']
    if room_key in rooms and len(rooms[room_key]) < 4:
        join_room(room_key)
        rooms[room_key].append(username)
        players[username] = {'room': room_key, 'points': 0}
        emit('joined_room', {'username': username, 'room_key': room_key}, room=room_key)
        if len(rooms[room_key]) == 4:
            emit('start_game', room=room_key)
    else:
        emit('error', {'message': 'Room is full or does not exist'})

@socketio.on('send_message')
def handle_message(data):
    room_key = data['room_key']
    message = data['message']
    emit('receive_message', {'message': message}, room=room_key)

if __name__ == '__main__':
    socketio.run(app, debug=True)
