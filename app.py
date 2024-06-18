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

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    username = data['username']
    if len(players) < 4:
        join_room(room_name)
        players[username] = {'card': None, 'points': 0, 'name': username}
        if len(players) == 4:
            emit('start_shuffle', room=room_name)
        emit('update', players, room=room_name)

@socketio.on('start_shuffle')
def start_shuffle():
    global round_counter, current_turn
    if round_counter < max_rounds:
        shuffled_cards = random.sample(cards, len(cards))
        for player, card in zip(players.values(), shuffled_cards):
            player['card'] = card.split('=')[1]
        round_counter += 1
        current_turn = (current_turn + 1) % 4
        emit('cards_assigned', players, room=room_name)
    if round_counter == max_rounds:
        emit('game_over', get_rankings(), room=room_name)

@socketio.on('king_order')
def king_order(data):
    king = data['king']
    command = data['command']
    emit('police_order', {'king': king, 'command': command}, room=room_name)

@socketio.on('police_action')
def police_action(data):
    police = data['police']
    target = data['target']
    command = data['command']
    king = data['king']

    # King always gets 900 points
    players[king]['points'] += points["King"]

    if players[target]['card'] == command:
        players[police]['points'] += points["Police"]
        players[target]['points'] = 0
    else:
        players[police]['points'] = 0
        players[target]['points'] += points[players[target]['card']]

    emit('update', players, room=room_name)
    emit('round_complete', players, room=room_name)

def get_rankings():
    ranking = sorted(players.items(), key=lambda x: x[1]['points'], reverse=True)
    return [{'username': user, 'points': data['points']} for user, data in ranking]

if __name__ == '__main__':
    socketio.run(app, debug=True)

