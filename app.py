from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

players = {}
cards = ["900=King", "800=Police", "600=Robbery", "400=Thief"]
points = {"King": 900, "Police": 800, "Robbery": 600, "Thief": 400}
round_counter = 0
max_rounds = 20
room_name = "game_room"
current_turn = 0
game_over = False

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    global game_over
    username = data['username']
    if not game_over and len(players) < 4:
        join_room(room_name)
        players[username] = {'card': None, 'points': 0, 'name': username}
        if len(players) == 4:
            emit('start_shuffle', {'round': round_counter + 1, 'max_rounds': max_rounds}, room=room_name)
        emit('update', {'players': players, 'round': round_counter + 1}, room=room_name)

@socketio.on('start_shuffle')
def start_shuffle():
    global round_counter, current_turn, game_over
    if not game_over:
        shuffled_cards = random.sample(cards, len(cards))
        for player, card in zip(players.values(), shuffled_cards):
            player['card'] = card.split('=')[1]
        round_counter += 1
        current_turn = (current_turn + 1) % 4
        emit('cards_assigned', {'players': players, 'round': round_counter, 'max_rounds': max_rounds}, room=room_name)
    if round_counter == max_rounds:
        game_over = True
        emit('game_over', {'rankings': get_rankings(), 'round': round_counter}, room=room_name)

@socketio.on('king_order')
def king_order(data):
    if not game_over:
        king = data['king']
        command = data['command']
        emit('police_order', {'king': king, 'command': command, 'round': round_counter}, room=room_name)

@socketio.on('police_action')
def police_action(data):
    if not game_over:
        police = data['police']
        target = data['target']
        command = data['command']
        king = data['king']

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

        emit('update', {'players': players, 'round': round_counter}, room=room_name)
        emit('round_complete', {'players': players, 'round': round_counter}, room=room_name)

@socketio.on('rematch')
def rematch():
    global round_counter, current_turn, game_over
    round_counter = 0
    current_turn = 0
    game_over = False
    for player in players.values():
        player['points'] = 0
    start_shuffle()

def get_rankings():
    ranking = sorted(players.items(), key=lambda x: x[1]['points'], reverse=True)
    return [{'username': user, 'points': data['points']} for user, data in ranking]

if __name__ == '__main__':
    socketio.run(app, debug=True)
