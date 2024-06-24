from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

rooms = {}

def generate_room_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/room/<room_key>')
def game_room(room_key):
    return render_template('game.html', room_key=room_key)

@socketio.on('create_room')
def on_create_room(data):
    room_key = generate_room_key()
    rooms[room_key] = {'players': {}, 'round_counter': 0, 'current_turn': 0, 'game_over': False}
    emit('room_created', {'room_key': room_key})

@socketio.on('join_room')
def on_join_room(data):
    room_key = data['room_key']
    username = data['username']
    if room_key in rooms and len(rooms[room_key]['players']) < 4:
        join_room(room_key)
        rooms[room_key]['players'][username] = {'card': None, 'points': 0, 'name': username}
        if len(rooms[room_key]['players']) == 4:
            emit('start_shuffle', {'round': rooms[room_key]['round_counter'] + 1, 'max_rounds': 20}, room=room_key)
        emit('update', {'players': rooms[room_key]['players'], 'round': rooms[room_key]['round_counter'] + 1}, room=room_key)

@socketio.on('start_shuffle')
def start_shuffle(data):
    room_key = data['room_key']
    room = rooms[room_key]
    if not room['game_over']:
        shuffled_cards = random.sample(["900=King", "800=Police", "600=Robbery", "400=Thief"], 4)
        for player, card in zip(room['players'].values(), shuffled_cards):
            player['card'] = card.split('=')[1]
        room['round_counter'] += 1
        room['current_turn'] = (room['current_turn'] + 1) % 4
        emit('cards_assigned', {'players': room['players'], 'round': room['round_counter'], 'max_rounds': 20}, room=room_key)
    if room['round_counter'] == 20:
        room['game_over'] = True
        emit('game_over', {'rankings': get_rankings(room_key), 'round': room['round_counter']}, room=room_key)

@socketio.on('king_order')
def king_order(data):
    room_key = data['room_key']
    if not rooms[room_key]['game_over']:
        king = data['king']
        command = data['command']
        emit('police_order', {'king': king, 'command': command, 'round': rooms[room_key]['round_counter']}, room=room_key)

@socketio.on('police_action')
def police_action(data):
    room_key = data['room_key']
    if not rooms[room_key]['game_over']:
        room = rooms[room_key]
        police = data['police']
        target = data['target']
        command = data['command']
        king = data['king']

        players = room['players']

        # King always gets 900 points added to their total
        players[king]['points'] += 900

        # Initialize role points to their default values
        police_points = 0
        robber_points = 600
        thief_points = 400

        if players[target]['card'].lower() == command.lower():
            police_points = 800
            players[target]['points'] = 0  # Target person gets zero points if caught
            if command.lower() == "robbery":
                robber_points = 0
            elif command.lower() == "thief":
                thief_points = 0
        else:
            police_points = 0

        # Update points
        players[police]['points'] += police_points
        for player, info in players.items():
            if player == target:
                continue
            if info['card'] == "Robbery" and info['points'] != 0:
                info['points'] += robber_points
            elif info['card'] == "Thief" and info['points'] != 0:
                info['points'] += thief_points

        emit('update', {'players': players, 'round': room['round_counter']}, room=room_key)
        emit('round_complete', {'players': players, 'round': room['round_counter']}, room=room_key)

@socketio.on('rematch')
def rematch(data):
    room_key = data['room_key']
    room = rooms[room_key]
    room['round_counter'] = 0
    room['current_turn'] = 0
    room['game_over'] = False
    for player in room['players'].values():
        player['points'] = 0
    start_shuffle({'room_key': room_key})

def get_rankings(room_key):
    room = rooms[room_key]
    ranking = sorted(room['players'].items(), key=lambda x: x[1]['points'], reverse=True)
    return [{'username': user, 'points': data['points']} for user, data in ranking]

if __name__ == '__main__':
    socketio.run(app, debug=True)
