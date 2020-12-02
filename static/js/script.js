var initiatives = [];
var turn_index = null;

$(document).ready(function() {
  // Use a "/test" namespace.
  // An application can open a connection on multiple namespaces, and
  // Socket.IO will multiplex all those connections on a single
  // physical channel. If you don't care about multiple channels, you
  // can set the namespace to an empty string.
  namespace = '/combat';
  
  // Connect to the Socket.IO server.
  // The connection URL has the following format, relative to the current page:
  //     http[s]://<domain>:<port>[/<namespace>]
  var socket = io(namespace);

  // TODO: Add room_id to all of the functions
  $('form#set_initiative').submit(function(event) {
    socket.emit('set_initiative', {character_name: $('#player_name').val(), init_val: $('#initiative_roll').val()});
    $('#initiative_roll').val(''); 
    return false;
  });

  $('form#send_chat').submit(function(event) {
    socket.emit('send_chat', {chat: $('#chat_text').val(), character_name: $('#player_name').val()});
    $('#chat_text').val(''); 
    return false;
  });
  
  $('form#start_battle').submit(function(event) {
    socket.emit('start_combat', {desc: "Start Battle"});
    return false;
  });
  
  $('form#end_battle').submit(function(event) {
    socket.emit('end_combat', {desc: "End Battle"});
    return false;
  });

  $('form#close_room').submit(function(event) {
    // TODO: fix this 
    if (window.confirm("This will clear all initiative and chat data for this room and kick players. Map and character token locations will be saved. Proceed?") ){
      socket.emit('end_room', {desc: "Close Room"});
      return false;
    }
    return false; 
  });
  
  $('form#end_turn').submit(function(event) {
    var next_index = null;
    if (turn_index + 1 == initiatives.length) {
      next_index = 0
    }
    else {
      next_index = turn_index + 1
    }
    socket.emit('end_turn', {desc: `${initiatives[turn_index][0]}'s Turn Ended`, old_name: initiatives[turn_index][0], next_name: initiatives[next_index][0]});
    return false;
  });

  socket.on('log_update', function(msg) {
    $('#log').append($('<div/>').text(msg.desc).html() + '<br>');
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

    initiatives.sort(function(a, b) { 
      return (b[1] - a[1]  ||  a[0].localeCompare(b[0]));
      // https://stackoverflow.com/questions/12900058/how-can-i-sort-a-javascript-array-of-objects-numerically-and-then-alphabetically
      // TODO: Fix the way name entry happens to conicide with SQL sort
    });

    var html_code = update_init_table();
    $('#initiative-table').html(html_code);
  });

  socket.on('chat_update', function(msg) {
    $('#chat-list').append($('<div/>').text(`${msg.character_name}: ${msg.chat}`).html() + '<br>');
  });

  socket.on('combat_started', function(msg) {
    // TODO: Decide if "End combat button" should replace start combat
    // button when combat started and vice versa
    var first_turn_name = msg.first_turn_name.split(" ").join("_");
    turn_index = 0;

    $('#log').append($('<div/>').text(msg.desc).html() + '<br>');
    $(`#${first_turn_name}-row`).addClass("bg-warning");

    $('#end_turn_button').prop('disabled', false);
    $('#set_initiative_button').prop('disabled', true);
    $('#start_battle_button').prop('disabled', true)
    $('#end_battle_button').prop('disabled', false);
  });

  socket.on('combat_ended', function(msg) {
    var current_turn_name = msg.current_turn_name.split(" ").join("_");

    $('#log').append($('<div/>').text(msg.desc).html() + '<br>');
    $(`#${current_turn_name}-row`).removeClass("bg-warning");

    $('#end_turn_button').prop('disabled', true);
    $('#set_initiative_button').prop('disabled', false);
    $('#start_battle_button').prop('disabled', false);
    $('#end_battle_button').prop('disabled', true)
    // TODO: Should it clear out the characters and send connected players to the home page?
  });

  socket.on('room_ended', function(msg) {
    // TODO: replace this link when going into development or deploying
    window.location.replace("/home");
  });

  socket.on('turn_ended', function(msg) {
    var next_index = null;
    if (turn_index + 1 == initiatives.length) {
      next_index = 0
    }
    else {
      next_index = turn_index + 1
    }
    var old_id = initiatives[turn_index][0].split(" ").join("_");
    var next_id = initiatives[next_index][0].split(" ").join("_");
    turn_index = next_index;

    $(`#${old_id}-row`).removeClass("bg-warning");
    $(`#${next_id}-row`).addClass("bg-warning");
    $('#log').append($('<div/>').text(msg.desc).html() + '<br>');
  });
});

function update_init_table() {
  code = "<tbody>";
  for (i = 0; i < initiatives.length; i++) {
    // TODO: Fix id to work when multiple characters have the same name
    var id = initiatives[i][0].split(" ").join("_");
    code += `<tr id=${id}-row><td>${initiatives[i][0]}</td><td>${initiatives[i][1]}</td></tr>`;
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

function onDragStart(event) {
  event.dataTransfer.setData('text/plain', event.target.id);
  // event.currentTarget.style.backgroundColor = 'yellow';
}

function onDragOver(event) {
  event.preventDefault();
}

function onDrop(event) {
  const id = "characterIcon";
  const draggableElement = document.getElementById(id);
  console.log(id)
  console.log(draggableElement)
  console.log(event)
  console.log(event.target)
  const dropzone = event.target;




  // draggableElement.style.position = "absolute"
  // dropzone.append(draggableElement);
  event.dataTransfer.clearData();
  var x = event.clientX;
  var y = event.clientY;
  var coor = "X coords: " + x + ", Y coords: " + y;
  console.log(coor)
  draggableElement.style.top = y + "px";
  draggableElement.style.left = x + "px";
} 