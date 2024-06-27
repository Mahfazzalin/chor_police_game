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

socket.on('start_game', () => {
    alert('Game is starting!');
});

socket.on('error', (data) => {
    alert(data.message);
});

function sendMessage() {
    const room_key = document.getElementById('room_key').value;
    const message = document.getElementById('message').value;
    socket.emit('send_message', { room_key: room_key, message: message });
}

socket.on('receive_message', (data) => {
    const messagesDiv = document.getElementById('messages');
    const messageElem = document.createElement('p');
    messageElem.innerText = data.message;
    messagesDiv.appendChild(messageElem);
});

function rematch() {
    // Logic for rematch goes here
}
