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

  $('form#set_initiative').submit(function(event) {
    socket.emit('set_initiative', {data: [$('#player_name').val(), $('#initiative_roll').val()]});
    return false;
  });

  $('form#send_chat').submit(function(event) {
    socket.emit('send_chat', {data: [$('#chat_text').val()]});
    return false;
  });

  socket.on('log_update', function(msg) {
    $('#log').append('<br>' + $('<div/>').text('Received ' + msg.data).html());
  });

  socket.on('initiative_update', function(msg) {
    $('#initiative-list').append('<br>' + $('<div/>').text('Received ' + msg.data).html());
  });

  socket.on('chat_update', function(msg) {
    $('#chat-list').append('<br>' + $('<div/>').text('Received ' + msg.data).html());
  });
});