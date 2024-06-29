# game version 1.0.4.9
# author: Mahfazzalin Shawon Reza
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

rooms = {}
cards = ["900=King", "800=Police", "600=Robbery", "400=Thief"]
points = {"King": 900, "Police": 800, "Robbery": 600, "Thief": 400}
round_counter = {}
max_rounds = 20

@app.route('/')
def index():
    return render_template('index.html')

def generate_room_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=random.randint(6, 8)))

@socketio.on('create_room')
def create_room():
    room_key = generate_room_key()
    while room_key in rooms:
        room_key = generate_room_key()
    rooms[room_key] = {
        'players': {},
        'round_counter': 0,
        'current_turn': 0
    }
    emit('room_created', {'room_key': room_key})

@socketio.on('join')
def on_join(data):
    username = data['username']
    room_key = data['room_key']
    if room_key in rooms:
        if len(rooms[room_key]['players']) < 4:
            join_room(room_key)
            rooms[room_key]['players'][username] = {'card': None, 'points': 0, 'name': username}
            emit('update', {'players': rooms[room_key]['players'], 'round': rooms[room_key]['round_counter'] + 1}, room=room_key)
            if len(rooms[room_key]['players']) == 4:
                emit('start_shuffle', {'round': rooms[room_key]['round_counter'] + 1, 'max_rounds': max_rounds}, room=room_key)
        else:
            emit('room_full')
    else:
        emit('room_not_found')

@socketio.on('start_shuffle')
def start_shuffle(data):
    room_key = data['room_key']
    if room_key in rooms:
        room = rooms[room_key]
        if room['round_counter'] < max_rounds:
            shuffled_cards = random.sample(cards, len(cards))
            for player, card in zip(room['players'].values(), shuffled_cards):
                player['card'] = card.split('=')[1]
            room['round_counter'] += 1
            room['current_turn'] = (room['current_turn'] + 1) % 4
            emit('cards_assigned', {'players': room['players'], 'round': room['round_counter'], 'max_rounds': max_rounds}, room=room_key)
        if room['round_counter'] == max_rounds:
            emit('game_over', {'rankings': get_rankings(room['players'])}, room=room_key)

@socketio.on('king_order')
def king_order(data):
    room_key = data['room_key']
    king = data['king']
    command = data['command']
    emit('police_order', {'king': king, 'command': command}, room=room_key)

@socketio.on('police_action')
def police_action(data):
    room_key = data['room_key']
    police = data['police']
    target = data['target']
    command = data['command']
    king = data['king']

    room = rooms[room_key]

    # King always gets 900 points added to their total
    room['players'][king]['points'] += points["King"]

    # Initialize role points to their default values
    police_points = 0
    robber_points = points["Robbery"]
    thief_points = points["Thief"]

    if room['players'][target]['card'].lower() == command.lower():
        police_points = points["Police"]
        room['players'][target]['points'] += 0  # Target person gets zero points if caught
        if command.lower() == "robbery":
            robber_points += 0
        elif command.lower() == "thief":
            thief_points += 0

    # Update points
    room['players'][police]['points'] += police_points
    for player, info in room['players'].items():
        if player == target:
            continue
        if info['card'] == "Robbery":
            info['points'] += robber_points
        elif info['card'] == "Thief":
            info['points'] += thief_points

    emit('update', {'players': room['players'], 'round': room['round_counter']}, room=room_key)
    emit('round_complete', {'players': room['players'], 'round': room['round_counter']}, room=room_key)

def get_rankings(players):
    ranking = sorted(players.items(), key=lambda x: x[1]['points'], reverse=True)
    return [{'username': user, 'points': data['points']} for user, data in ranking]

@socketio.on('send_message')
def handle_send_message(data):
    room_key = data['room_key']
    message = data['message']
    username = data['username']
    emit('receive_message', {'username': username, 'message': message}, room=room_key)

if __name__ == '__main__':
    socketio.run(app, debug=True)
