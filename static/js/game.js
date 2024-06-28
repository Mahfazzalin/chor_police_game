const socket = io();

function createRoom() {
    const username = document.getElementById('username').value;
    socket.emit('create_room', { username: username });
}

function joinRoom() {
    const username = document.getElementById('username').value;
    const room_key = document.getElementById('room_key').value;
    socket.emit('join_room', { username: username, room_key: room_key });
}

socket.on('room_created', (data) => {
    alert(`Room created with key: ${data.room_key}`);
    document.getElementById('join_game').classList.add('hidden');
    document.getElementById('game_dashboard').classList.remove('hidden');
});

socket.on('joined_room', (data) => {
    alert(`Joined room: ${data.room_key}`);
    document.getElementById('join_game').classList.add('hidden');
    document.getElementById('game_dashboard').classList.remove('hidden');
});

socket.on('all_players_joined', () => {
    alert('All players joined. Starting game...');
    document.getElementById('start_shuffle').classList.remove('hidden');
});

function startShuffle() {
    const room_key = document.getElementById('room_key').value;
    socket.emit('start_shuffle', { room_key: room_key });
}

socket.on('cards_assigned', (data) => {
    alert(`Cards assigned: ${JSON.stringify(data)}`);
    const username = document.getElementById('username').value;
    alert(`Your card: ${data[username]}`);
});

socket.on('roles_assigned', (data) => {
    alert(`King: ${data.king}, Police: ${data.police}`);
    if (data.king === document.getElementById('username').value) {
        const target = prompt("Who will Police catch? (Enter player name)");
        socket.emit('king_decision', { room_key: document.getElementById('room_key').value, target: target });
    }
});

socket.on('round_result', (data) => {
    alert(`Police caught ${data.target}. Points: ${JSON.stringify(data.points)}`);
    document.getElementById('points').innerText = `Points: ${JSON.stringify(data.points)}`;
});

socket.on('next_shuffle', (data) => {
    alert(`Next shuffle by: ${data.current_player}`);
    if (data.current_player === document.getElementById('username').value) {
        document.getElementById('start_shuffle').classList.remove('hidden');
    }
});

socket.on('game_over', (data) => {
    alert(`Game over! Winner: ${data.winner}. Points: ${JSON.stringify(data.points)}`);
    document.getElementById('game_dashboard').classList.add('hidden');
    document.getElementById('game_over').classList.remove('hidden');
});

socket.on('receive_message', (data) => {
    const messagesDiv = document.getElementById('messages');
    const messageElem = document.createElement('p');
    messageElem.innerText = data.message;
    messagesDiv.appendChild(messageElem);
});

function sendMessage() {
    const room_key = document.getElementById('room_key').value;
    const message = document.getElementById('message').value;
    socket.emit('send_message', { room_key: room_key, message: message });
}

function rematch() {
    // Logic for rematch goes here
}
