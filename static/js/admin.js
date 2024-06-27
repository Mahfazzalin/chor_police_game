var socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('connect', function() {
    socket.emit('get_stats');
});

socket.on('stats', function(data) {
    document.getElementById('rooms_today').innerText = data.rooms_today;
    document.getElementById('rooms_week').innerText = data.rooms_week;
    document.getElementById('rooms_month').innerText = data.rooms_month;
    document.getElementById('rooms_year').innerText = data.rooms_year;
    document.getElementById('active_rooms').innerText = data.active_rooms;
    document.getElementById('active_players').innerText = data.active_players;
});
