from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

rooms = {}
players = {}
admin_stats = {
    'rooms_created_today': 0,
    'rooms_created_week': 0,
    'rooms_created_month': 0,
    'rooms_created_year': 0,
    'active_rooms': 0,
    'active_players': 0,
    'total_players_today': 0
}
cards = ["900=King", "800=Police", "600=Robbery", "400=Thief"]
points = {"King": 900, "Police": 800, "Robbery": 600, "Thief": 400}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

def update_admin_stats():
    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)
    return {
        'rooms_created_today': admin_stats['rooms_created_today'],
        'rooms_created_week': admin_stats['rooms_created_week'],
        'rooms_created_month': admin_stats['rooms_created_month'],
        'rooms_created_year': admin_stats['rooms_created_year'],
        'active_rooms': admin_stats['active_rooms'],
        'active_players': admin_stats['active_players'],
        'total_players_today': admin_stats['total_players_today']
    }

@socketio.on('create_room')
def on_create_room(data):
    room = data['room']
    username = data['username']
    join_room(room)
    if room not in rooms:
        rooms[room] = {
            'players': {},
            'round_counter': 0,
            'max_rounds': 20,
            'current_turn': 0,
            'game_over': False,
            'messages': []
        }
        admin_stats['rooms_created_today'] += 1
        admin_stats['rooms_created_week'] += 1
        admin_stats['rooms_created_month'] += 1
        admin_stats['rooms_created_year'] += 1
        admin_stats['active_rooms'] += 1
    rooms[room]['players'][username] = {'card': None, 'points': 0, 'name': username}
    players[username] = room
    admin_stats['active_players'] += 1
    admin_stats['total_players_today'] += 1
    emit('room_created', {'room': room, 'username': username}, room=room)
    emit('update', {'players': rooms[room]['players'], 'round': rooms[room]['round_counter'] + 1}, room=room)

@socketio.on('join_room')
def on_join(data):
    room = data['room']
    username = data['username']
    if room in rooms and len(rooms[room]['players']) < 4 and not rooms[room]['game_over']:
        join_room(room)
        rooms[room]['players'][username] = {'card': None, 'points': 0, 'name': username}
        players[username] = room
        admin_stats['active_players'] += 1
        emit('player_joined', {'room': room, 'username': username}, room=room)
        if len(rooms[room]['players']) == 4:
            emit('start_shuffle', {'round': rooms[room]['round_counter'] + 1, 'max_rounds': rooms[room]['max_rounds']}, room=room)
        emit('update', {'players': rooms[room]['players'], 'round': rooms[room]['round_counter'] + 1}, room=room)

@socketio.on('start_shuffle')
def start_shuffle(data):
    room = data['room']
    if room in rooms and not rooms[room]['game_over']:
        shuffled_cards = random.sample(cards, len(cards))
        for player, card in zip(rooms[room]['players'].values(), shuffled_cards):
            player['card'] = card.split('=')[1]
        rooms[room]['round_counter'] += 1
        rooms[room]['current_turn'] = (rooms[room]['current_turn'] + 1) % 4
        emit('cards_assigned', {'players': rooms[room]['players'], 'round': rooms[room]['round_counter'], 'max_rounds': rooms[room]['max_rounds']}, room=room)
    if rooms[room]['round_counter'] == rooms[room]['max_rounds']:
        rooms[room]['game_over'] = True
        emit('game_over', {'rankings': get_rankings(room), 'round': rooms[room]['round_counter']}, room=room)

@socketio.on('king_order')
def king_order(data):
    room = data['room']
    if room in rooms and not rooms[room]['game_over']:
        king = data['king']
        command = data['command']
        emit('police_order', {'king': king, 'command': command, 'round': rooms[room]['round_counter']}, room=room)

@socketio.on('police_action')
def police_action(data):
    room = data['room']
    if room in rooms and not rooms[room]['game_over']:
        police = data['police']
        target = data['target']
        command = data['command']
        king = data['king']

        # King always gets 900 points added to their total
        rooms[room]['players'][king]['points'] += points["King"]

        # Initialize role points to their default values
        police_points = 0
        robber_points = points["Robbery"]
        thief_points = points["Thief"]

        if rooms[room]['players'][target]['card'].lower() == command.lower():
            police_points = points["Police"]
            rooms[room]['players'][target]['points'] = 0  # Target person gets zero points if caught
            if command.lower() == "robbery":
                robber_points = 0
            elif command.lower() == "thief":
                thief_points = 0

        # Update points
        rooms[room]['players'][police]['points'] += police_points
        for player, info in rooms[room]['players'].items():
            if player == target:
                continue
            if info['card'] == "Robbery":
                info['points'] += robber_points
            elif info['card'] == "Thief":
                info['points'] += thief_points

        emit('update', {'players': rooms[room]['players'], 'round': rooms[room]['round_counter']}, room=room)
        emit('round_complete', {'players': rooms[room]['players'], 'round': rooms[room]['round_counter']}, room=room)

@socketio.on('send_message')
def send_message(data):
    room = data['room']
    username = data['username']
    message = data['message']
    if room in rooms:
        rooms[room]['messages'].append({'username': username, 'message': message})
        emit('new_message', {'username': username, 'message': message}, room=room)

@socketio.on('rematch')
def rematch(data):
    room = data['room']
    if room in rooms:
        rooms[room]['round_counter'] = 0
        rooms[room]['current_turn'] = 0
        rooms[room]['game_over'] = False
        for player in rooms[room]['players'].values():
            player['points'] = 0
        emit('start_shuffle', {'round': rooms[room]['round_counter'] + 1, 'max_rounds': rooms[room]['max_rounds']}, room=room)

@socketio.on('disconnect')
def on_disconnect():
    username = request.sid
    if username in players:
        room = players[username]
        leave_room(room)
        del rooms[room]['players'][username]
        if not rooms[room]['players']:
            del rooms[room]
            admin_stats['active_rooms'] -= 1
        admin_stats['active_players'] -= 1
        del players[username]

def get_rankings(room):
    ranking = sorted(rooms[room]['players'].items(), key=lambda x: x[1]['points'], reverse=True)
    return [{'username': user, 'points': data['points']} for user, data in ranking]

@socketio.on('get_admin_stats')
def get_admin_stats():
    emit('admin_stats', update_admin_stats())

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
