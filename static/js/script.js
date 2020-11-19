var initiatives = [];

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
    socket.emit('set_initiative', {character_name: $('#player_name').val(), init_val: $('#initiative_roll').val()});
    return false;
  });

  $('form#send_chat').submit(function(event) {
    socket.emit('send_chat', {data: [$('#chat_text').val()]});
    return false;
  });

  socket.on('log_update', function(msg) {
    $('#log').append($('<div/>').text(msg.data).html() + '<br>');
  });

  socket.on('initiative_update', function(msg) {
    // TODO: Fix to allow multiple players have the same character name
    var updated = false;

    for (i = 0; i < initiatives.length; i++) {
      if (initiatives[i][0] == msg.character_name) {
        initiatives[i][1] = msg.init_val;
        updated = true;
      }
    }

    if (!updated) {
      initiatives.push([msg.character_name, msg.init_val]);
    }

    initiatives.sort(compareSecondColumn);

    var html_code = update_init_table();
    $('#initiative-table').html(html_code);
  });

  socket.on('chat_update', function(msg) {
    $('#chat-list').append($('<div/>').text(msg.data).html() + '<br>');
  });
});

function update_init_table() {
  code = "<tbody>";
  for (i = 0; i < initiatives.length; i++) {
    code += `<tr><td>${initiatives[i][0]}</td><td>${initiatives[i][1]}</td></tr>`;
  }

  code += "</tbody>";

  return code;
}

function compareSecondColumn(a, b) {
  if (a[1] === b[1]) {
      return 0;
  }
  else {
      return (a[1] > b[1]) ? -1 : 1;
  }
}