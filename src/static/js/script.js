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
    var tableData = '<tr><td>{0}</td><td>{1}</td></tr>'.format(msg.data[0], msg.data[1]);
    $('#initiative-table').append(tableData);
  });

  socket.on('chat_update', function(msg) {
    $('#chat-list').append('<br>' + $('<div/>').text(msg.data).html());
  });
  $('form#api_call').submit(function(event) {
    socket.emit('api_call', {data: $('AAAA').val()});
    return false;
  }); 
  socket.on('api_call', function(msg) {
    $('#chat-list').append('<br>' + $('<div/>').text('API: ' + msg.data).html());
  })
});

function loadDoc() {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      document.getElementById("demo").innerHTML = this.responseText;
    }
  };
  xhttp.open("GET", "https://www.dnd5eapi.co/api/", true);
  xhttp.send();
  $('#chat-list').append('<br>' + $('<div/>').text('Received ' + msg.data).html());
}
});

String.prototype.format = function () {
  var args = arguments;
  return this.replace(/\{(\d+)\}/g, function (m, n) { return args[n]; });
};