// function addPlayer() {
//   let playerName = document.querySelector("#player_name").value;
//   let initiative = document.querySelector("#initiative_roll").value;

//   console.log(playerName, initiative);
// }

$(document).ready(function() {
  // Use a "/test" namespace.
  // An application can open a connection on multiple namespaces, and
  // Socket.IO will multiplex all those connections on a single
  // physical channel. If you don't care about multiple channels, you
  // can set the namespace to an empty string.
  namespace = '/test';
  
  // Connect to the Socket.IO server.
  // The connection URL has the following format, relative to the current page:
  //     http[s]://<domain>:<port>[/<namespace>]
  var socket = io(namespace);

  socket.on('connect', function() {
    socket.emit('my_event', {data: 'I\'m connected!'});
  });

  $('form#set_initiative').submit(function(event) {
    socket.emit('my_broadcast_event', {data: [$('#player_name').val(), $('#initiative_roll').val()]});
    // console.log([$('#player_name').val(), $('#initiative_roll').val()])
    return false;
  });

  socket.on('my_response', function(msg) {
    $('#initiative-list').append('<br>' + $('<div/>').text('Received ' + msg.data).html());
  });
});

// function openNav(id) {
//     document.getElementById("initiative").style.width = "16.66666667%";
//   }
  
//   function closeNav(id) {
//     document.getElementById("initiative").style.width = "0";
//   } 

// function openTools(id) {
//     document.getElementById("dm-tools").style.width = "16.66666667%";
// }

// function closeTools(id) {
//     document.getElementById("dm-tools").style.width = "0";
//   } 

// function openLogs(id) {
//     document.getElementById("log").style.height = "16.66666667%";
// }

// function closeLogs(id) {
//     document.getElementById("log").style.height = "0";
// }