# Chor Police - Web Version v2.1
# Original game by Mahfazzalin Shawon Reza

from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chor-police-secret-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}
CARDS = ["King", "Police", "Robbery", "Thief"]
POINTS = {"King": 900, "Police": 800, "Robbery": 600, "Thief": 400}
MAX_ROUNDS = 20


def generate_room_key():
    while True:
        key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if key not in rooms:
            return key


def get_rankings(players):
    ranking = sorted(players.items(), key=lambda x: x[1]['points'], reverse=True)
    return [{'username': user, 'points': data['points']} for user, data in ranking]


def sanitize_players(players):
    return {k: {'card': v['card'], 'points': v['points'], 'name': v['name']} for k, v in players.items()}


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('create_room')
def create_room():
    room_key = generate_room_key()
    rooms[room_key] = {
        'players': {},
        'round_counter': 0,
        'host': None,
        'order_command': None,
    }
    emit('room_created', {'room_key': room_key})


@socketio.on('join')
def on_join(data):
    username = data.get('username', '').strip()
    room_key = data.get('room_key', '').strip().upper()

    if not username or not room_key:
        emit('error', {'message': 'Name and room key are required.'})
        return
    if room_key not in rooms:
        emit('room_not_found')
        return

    room = rooms[room_key]

    if len(room['players']) >= 4:
        emit('room_full')
        return

    join_room(room_key)
    room['players'][username] = {'card': None, 'points': 0, 'name': username}

    if room['host'] is None:
        room['host'] = username

    emit('update', {
        'players': sanitize_players(room['players']),
        'round': room['round_counter'],
        'host': room['host'],
    }, room=room_key)

    if len(room['players']) == 4:
        emit('start_shuffle', {
            'round': room['round_counter'] + 1,
            'max_rounds': MAX_ROUNDS,
            'host': room['host'],
        }, room=room_key)


@socketio.on('start_shuffle')
def start_shuffle(data):
    room_key = data.get('room_key', '').upper()
    if room_key not in rooms:
        return

    room = rooms[room_key]

    if room['round_counter'] >= MAX_ROUNDS:
        emit('game_over', {
            'round': room['round_counter'],
            'rankings': get_rankings(room['players']),
        }, room=room_key)
        return

    shuffled = random.sample(CARDS, len(CARDS))
    for player, card in zip(room['players'].values(), shuffled):
        player['card'] = card

    room['round_counter'] += 1
    room['order_command'] = None

    emit('cards_assigned', {
        'players': sanitize_players(room['players']),
        'round': room['round_counter'],
        'max_rounds': MAX_ROUNDS,
        'host': room['host'],
    }, room=room_key)


@socketio.on('king_order')
def king_order(data):
    room_key = data.get('room_key', '').upper()
    command = data.get('command', '')
    if room_key not in rooms:
        return
    if command not in ('Thief', 'Robbery'):
        return
    rooms[room_key]['order_command'] = command
    emit('police_order', {'king': data.get('king'), 'command': command}, room=room_key)


@socketio.on('police_action')
def police_action(data):
    room_key = data.get('room_key', '').upper()
    police  = data.get('police')
    target  = data.get('target')
    command = data.get('command')
    king    = data.get('king')

    if room_key not in rooms:
        return

    room    = rooms[room_key]
    players = room['players']

    if police not in players or target not in players or king not in players:
        return

    target_card   = players[target]['card']
    correct_catch = target_card.lower() == command.lower()

    # King always earns their points every round
    players[king]['points'] += POINTS['King']

    if correct_catch:
        # Police caught the RIGHT person:
        #   Police  → gets Police points (800)
        #   Target  → gets 0
        #   Others  → get their own card's points
        players[police]['points'] += POINTS['Police']
        for name, info in players.items():
            if name in (king, police, target):
                continue
            players[name]['points'] += POINTS[info['card']]
        # target stays at +0
    else:
        # Police caught the WRONG person:
        #   Police  → gets 0
        #   Target  → gets their own card's points (they were wrongly caught)
        #   Others  → get their own card's points
        players[target]['points'] += POINTS[target_card]
        for name, info in players.items():
            if name in (king, police, target):
                continue
            players[name]['points'] += POINTS[info['card']]
        # police stays at +0

    emit('round_complete', {
        'players':       sanitize_players(players),
        'round':         room['round_counter'],
        'max_rounds':    MAX_ROUNDS,
        'correct_catch': correct_catch,
        'target':        target,
        'command':       command,
        'target_card':   target_card,
    }, room=room_key)

    if room['round_counter'] >= MAX_ROUNDS:
        emit('game_over', {
            'round':    room['round_counter'],
            'rankings': get_rankings(players),
        }, room=room_key)


@socketio.on('send_message')
def handle_message(data):
    room_key = data.get('room_key', '').upper()
    emit('receive_message', {
        'username': data.get('username'),
        'message':  data.get('message', ''),
    }, room=room_key)


if __name__ == '__main__':
    socketio.run(app, debug=True)
