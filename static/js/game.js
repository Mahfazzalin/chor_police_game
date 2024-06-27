var socket = io();
var username;
var room;
var players = {};
var roundNumber = 0;
var maxRounds = 20;
var king, police;

function joinGame() {
    username = document.getElementById('username').value;
    room = document.getElementById('room').value;
    if (username && room) {
        socket.emit('join_room', {'username': username, 'room': room});
        document.getElementById('join-game').classList.add('hidden');
        document.getElementById('dashboard').classList.remove('hidden');
    }
}

function createRoom() {
    username = document.getElementById('username').value;
    room = 'room-' + Math.floor(Math.random() * 10000);
    if (username) {
        socket.emit('create_room', {'username': username, 'room': room});
        document.getElementById('join-game').classList.add('hidden');
        document.getElementById('dashboard').classList.remove('hidden');
    }
}

socket.on('room_created', function(data) {
    room = data.room;
    username = data.username;
});

socket.on('player_joined', function(data) {
    updatePlayerList(data.room, data.username);
});

function updatePlayerList(room, username) {
    var playersDiv = document.getElementById('players');
    playersDiv.innerHTML += `<p>${username} joined the room ${room}</p>`;
}

socket.on('start_shuffle', function(data) {
    roundNumber = data.round;
    maxRounds = data.max_rounds;
    document.getElementById('round-number').innerText = `Round ${roundNumber}/${maxRounds}`;
    socket.emit('start_shuffle', { 'room': room });
});

socket.on('cards_assigned', function(data) {
    players = data.players;
    var cardsDiv = document.getElementById('cards');
    var commandsDiv = document.getElementById('commands');
    cardsDiv.innerHTML = `<p>Your card: ${players[username].card}</p>`;
    commandsDiv.innerHTML = '';

    if (players[username].card === 'King') {
        commandsDiv.innerHTML = `
            <button onclick="giveOrder('Thief')" class="bg-blue-500 text-white p-2">Catch Thief</button>
            <button onclick="giveOrder('Robbery')" class="bg-blue-500 text-white p-2">Catch Robber</button>
        `;
    } else if (players[username].card === 'Police') {
        police = username;
        commandsDiv.innerHTML = '<p>Waiting for King\'s order...</p>';
    }
});

function giveOrder(command) {
    socket.emit('king_order', { 'king': username, 'command': command, 'room': room });
}

socket.on('police_order', function(data) {
    var dashboard = document.getElementById('commands');
    dashboard.innerHTML = '';

    if (username === data.command) {
        var options = Object.keys(players).filter(p => p !== username && players[p].card !== 'King').map(p => 
            `<button onclick="policeAction('${p}', '${data.command}')" class="bg-red-500 text-white p-2 mt-2">Catch ${p}</button>`
        ).join('');
        dashboard.innerHTML += `<p>As Police, choose a player to catch</p>${options}`;
    }
});

function policeAction(target, command) {
    socket.emit('police_action', { 'police': username, 'target': target, 'command': command, 'room': room });
}

socket.on('update', function(data) {
    players = data.players;
    var dashboard = document.getElementById('points');
    dashboard.innerHTML = Object.keys(players).map(player => 
        `<p>${player} (${players[player].card}): ${players[player].points} points</p>`
    ).join('');
});

socket.on('round_complete', function(data) {
    players = data.players;
    roundNumber = data.round;
    document.getElementById('round-number').innerText = `Round ${roundNumber}/${maxRounds}`;
});

function sendMessage() {
    var message = document.getElementById('message').value;
    socket.emit('send_message', { 'username': username, 'message': message, 'room': room });
    document.getElementById('message').value = '';
}

socket.on('new_message', function(data) {
    var messagesDiv = document.getElementById('messages');
    messagesDiv.innerHTML += `<p><strong>${data.username}:</strong> ${data.message}</p>`;
});

socket.on('game_over', function(data) {
    document.getElementById('dashboard').classList.add('hidden');
    document.getElementById('game-over').classList.remove('hidden');
    document.getElementById('game-over-round').innerText = `Game Over after ${data.round} rounds`;
    var rankings = data.rankings.map((rank, i) => 
        `<p>${i + 1}. ${rank.username}: ${rank.points} points</p>`
    ).join('');
    document.getElementById('rankings').innerHTML = rankings;
});

function rematchGame() {
    socket.emit('rematch', { 'room': room });
    document.getElementById('game-over').classList.add('hidden');
    document.getElementById('dashboard').classList.remove('hidden');
}
