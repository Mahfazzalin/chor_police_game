#game version 1.0.4.9
#auther: Mahfazzalin Shawon Reza
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

players = {}
rooms = {}
cards = ["900=King", "800=Police", "600=Robbery", "400=Thief"]
points = {"King": 900, "Police": 800, "Robbery": 600, "Thief": 400}
round_counter = 0
max_rounds = 20
current_turn = 0

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create_room')
def create_room(data):
    room_key = data['room_key']
    username = data['username']
    if room_key not in rooms:
        rooms[room_key] = {'players': {}, 'round_counter': 0, 'current_turn': 0}
        join_room(room_key)
        rooms[room_key]['players'][username] = {'card': None, 'points': 0, 'name': username}
        emit('room_created', {'room_key': room_key, 'username': username})
    else:
        emit('error', {'message': 'Room already exists.'})

@socketio.on('join_room')
def join_room_handler(data):
    room_key = data['room_key']
    username = data['username']
    if room_key in rooms and len(rooms[room_key]['players']) < 4:
        join_room(room_key)
        rooms[room_key]['players'][username] = {'card': None, 'points': 0, 'name': username}
        emit('joined_room', {'room_key': room_key, 'username': username}, room=room_key)
        if len(rooms[room_key]['players']) == 4:
            emit('start_shuffle', {'round': rooms[room_key]['round_counter'] + 1, 'max_rounds': max_rounds}, room=room_key)
        emit('update', {'players': rooms[room_key]['players'], 'round': rooms[room_key]['round_counter'] + 1}, room=room_key)
    else:
        emit('error', {'message': 'Room is full or does not exist.'})

@socketio.on('start_shuffle')
def start_shuffle(data):
    room_key = data['room_key']
    if rooms[room_key]['round_counter'] < max_rounds:
        shuffled_cards = random.sample(cards, len(cards))
        for player, card in zip(rooms[room_key]['players'].values(), shuffled_cards):
            player['card'] = card.split('=')[1]
        rooms[room_key]['round_counter'] += 1
        rooms[room_key]['current_turn'] = (rooms[room_key]['current_turn'] + 1) % 4
        emit('cards_assigned', {'players': rooms[room_key]['players'], 'round': rooms[room_key]['round_counter'], 'max_rounds': max_rounds}, room=room_key)
    if rooms[room_key]['round_counter'] == max_rounds:
        emit('game_over', {'rankings': get_rankings(room_key), 'round': rooms[room_key]['round_counter']}, room=room_key)

@socketio.on('king_order')
def king_order(data):
    room_key = data['room_key']
    king = data['king']
    command = data['command']
    emit('police_order', {'king': king, 'command': command, 'round': rooms[room_key]['round_counter']}, room=room_key)

@socketio.on('police_action')
def police_action(data):
    room_key = data['room_key']
    police = data['police']
    target = data['target']
    command = data['command']
    king = data['king']

    players = rooms[room_key]['players']

    # King always gets 900 points added to their total
    players[king]['points'] += points["King"]

    # Initialize role points to their default values
    police_points = 0
    robber_points = points["Robbery"]
    thief_points = points["Thief"]

    if players[target]['card'].lower() == command.lower():
        police_points = points["Police"]
        players[target]['points'] += 0  # Target person gets zero points if caught
        if command.lower() == "robbery":
            robber_points += 0
        elif command.lower() == "thief":
            thief_points += 0

    # Update points
    players[police]['points'] += police_points
    for player, info in players.items():
        if player == target:
            continue
        if info['card'] == "Robbery":
            info['points'] += robber_points
        elif info['card'] == "Thief":
            info['points'] += thief_points

    emit('update', {'players': players, 'round': rooms[room_key]['round_counter']}, room=room_key)
    emit('round_complete', {'players': players, 'round': rooms[room_key]['round_counter']}, room=room_key)

@socketio.on('send_message')
def handle_message(data):
    room_key = data['room_key']
    message = data['message']
    emit('receive_message', {'username': data['username'], 'message': message}, room=room_key)

def get_rankings(room_key):
    ranking = sorted(rooms[room_key]['players'].items(), key=lambda x: x[1]['points'], reverse=True)
    return [{'username': user, 'points': data['points']} for user, data in ranking]

if __name__ == '__main__':
    socketio.run(app, debug=True)
