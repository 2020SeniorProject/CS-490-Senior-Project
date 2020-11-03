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
});

String.prototype.format = function () {
  var args = arguments;
  return this.replace(/\{(\d+)\}/g, function (m, n) { return args[n]; });
};

async function getData(url) {
  return fetch(url)
  .then(response => response.json())
  .catch(error => console.log(error));
}

async function apiTest(url) {
  let data = await Promise.all([getData(url)]);
  // console.log(data[0]); 
  document.querySelector("#demo").innerHTML = "";
  $('#demo').append($('<div/>').text("Classes:").html() + '<br>')
  for (i = 0; i < data[0].count; i++) {
    $('#demo').append('<br>' + $('<div/>').text(data[0].results[i].name).html())
  }
}