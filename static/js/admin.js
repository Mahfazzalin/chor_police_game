document.addEventListener("DOMContentLoaded", function () {
    var socket = io();

    function updateAdminStats(data) {
        document.getElementById('rooms-today').innerText = data.rooms_created_today;
        document.getElementById('rooms-week').innerText = data.rooms_created_week;
        document.getElementById('rooms-month').innerText = data.rooms_created_month;
        document.getElementById('rooms-year').innerText = data.rooms_created_year;
        document.getElementById('active-rooms').innerText = data.active_rooms;
        document.getElementById('active-players').innerText = data.active_players;
        document.getElementById('total-players-today').innerText = data.total_players_today;
    }

    // Request stats on load
    socket.emit('get_admin_stats');

    // Update stats on receiving admin_stats event
    socket.on('admin_stats', function (data) {
        updateAdminStats(data);
    });

    // Optionally, set an interval to request stats periodically
    setInterval(function () {
        socket.emit('get_admin_stats');
    }, 60000); // Update every minute
});
