from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

players = {}
rooms = {}
room_count = 0
cards = ["900=King", "800=Police", "600=Robbery", "400=Thief"]

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create_room')
def create_room(data):
    global room_count
    room_count += 1
    room_key = f"room{room_count}"
    rooms[room_key] = {'players': [data['username']], 'round': 0, 'current_player': 0}
    join_room(room_key)
    players[data['username']] = {'room': room_key, 'points': 0, 'card': None}
    emit('room_created', {'room_key': room_key, 'username': data['username']})

@socketio.on('join_room')
def join(data):
    room_key = data['room_key']
    username = data['username']
    if room_key in rooms and len(rooms[room_key]['players']) < 4:
        join_room(room_key)
        rooms[room_key]['players'].append(username)
        players[username] = {'room': room_key, 'points': 0, 'card': None}
        emit('joined_room', {'username': username, 'room_key': room_key}, room=room_key)
        if len(rooms[room_key]['players']) == 4:
            emit('all_players_joined', room=room_key)
    else:
        emit('error', {'message': 'Room is full or does not exist'})

@socketio.on('start_shuffle')
def start_shuffle(data):
    room_key = data['room_key']
    if room_key in rooms:
        shuffle_and_assign_cards(room_key)

def shuffle_and_assign_cards(room_key):
    random.shuffle(cards)
    for i, player in enumerate(rooms[room_key]['players']):
        players[player]['card'] = cards[i]
    emit('cards_assigned', {player: players[player]['card'] for player in rooms[room_key]['players']}, room=room_key)
    king = next(player for player in rooms[room_key]['players'] if players[player]['card'] == "900=King")
    police = next(player for player in rooms[room_key]['players'] if players[player]['card'] == "800=Police")
    emit('roles_assigned', {'king': king, 'police': police}, room=room_key)

@socketio.on('king_decision')
def king_decision(data):
    room_key = data['room_key']
    target = data['target']
    king = next(player for player in rooms[room_key]['players'] if players[player]['card'] == "900=King")
    police = next(player for player in rooms[room_key]['players'] if players[player]['card'] == "800=Police")
    if players[target]['card'] in ["600=Robbery", "400=Thief"]:
        players[police]['points'] += 800
        players[target]['points'] = 0
    else:
        players[police]['points'] = 0
        players[target]['points'] += int(players[target]['card'].split('=')[0])
    emit('round_result', {'police': police, 'target': target, 'points': {player: players[player]['points'] for player in rooms[room_key]['players']}}, room=room_key)
    rooms[room_key]['round'] += 1
    if rooms[room_key]['round'] < 20:
        rooms[room_key]['current_player'] = (rooms[room_key]['current_player'] + 1) % 4
        emit('next_shuffle', {'current_player': rooms[room_key]['players'][rooms[room_key]['current_player']]}, room=room_key)
    else:
        winner = max(rooms[room_key]['players'], key=lambda player: players[player]['points'])
        emit('game_over', {'winner': winner, 'points': {player: players[player]['points'] for player in rooms[room_key]['players']}}, room=room_key)

@socketio.on('send_message')
def handle_message(data):
    room_key = data['room_key']
    message = data['message']
    emit('receive_message', {'message': message}, room=room_key)

if __name__ == '__main__':
    socketio.run(app, debug=True)
