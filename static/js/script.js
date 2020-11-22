var initiatives = [];
var turn_index = null;

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

  $('form#start_battle').submit(function(event) {
    // TODO: Add in the room_id for processing
    console.log("Started battle")
    socket.emit('start_combat', {data: "Start Battle"});
    return false;
  });

  $('form#end_battle').submit(function(event) {
    console.log("Ended battle")
    socket.emit('end_combat', {data: "End Battle"});
    return false;
  });

  $('form#end_turn').submit(function(event) {
    // TODO: Add in the room_id for processing
    console.log("Turn ended")
    var next_index = null;
    if (turn_index + 1 == initiatives.length) {
      next_index = 0
    }
    else {
      next_index = turn_index + 1
    }
    socket.emit('end_turn', {data: `${initiatives[turn_index][0]}'s Turn Ended`, old_name: initiatives[turn_index][0], next_name: initiatives[next_index][0]});
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

  socket.on('combat_started', function(msg) {
    $('#log').append($('<div/>').text(msg.data).html() + '<br>');
    $(`#${msg.first_turn_name}-row`).addClass("bg-warning");
    turn_index = 0;
    $('#end_turn_button').prop('disabled', false);
    $('#set_initiative_button').prop('disabled', true);
    $('#start_battle').prop('disabled', true)
    $('#end_battle').prop('disabled', true);
    // TODO: Update "start_battle" form to "end_battle" and add socketio events
  });

  socket.on('combat_ended', function(msg) {
    $('#log').append($('<div/>').text(msg.data).html() + '<br>');
    $(`#${msg.current_turn_player}-row`).removeClass("bg-warning");
    turn_index = null;
    $('#end_turn_button').prop('disabled', true);
    $('#set_initiative_button').prop('disabled', false);
    $('#start_battle').prop('disabled', false);
    $('#end_battle').prop('disabled', true)
  });

  socket.on('turn_ended', function(msg) {
    $('#log').append($('<div/>').text(msg.data).html() + '<br>');
    var next_index = null;
    if (turn_index + 1 == initiatives.length) {
      next_index = 0
    }
    else {
      next_index = turn_index + 1
    }
    $(`#${initiatives[turn_index][0]}-row`).removeClass("bg-warning");
    $(`#${initiatives[next_index][0]}-row`).addClass("bg-warning");
    turn_index = next_index;
  });
});

function update_init_table() {
  code = "<tbody>";
  for (i = 0; i < initiatives.length; i++) {
    // TODO: Fix id to work when multiple characters have the same name
    code += `<tr id=${initiatives[i][0]}-row><td>${initiatives[i][0]}</td><td>${initiatives[i][1]}</td></tr>`;
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
  //https://stackoverflow.com/questions/16096872/how-to-sort-2-dimensional-array-by-column-value
}