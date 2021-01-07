/*jshint esversion: 6 */


$(document).ready(function() {
  // Use a "/test" namespace.
  // An application can open a connection on multiple namespaces, and
  // Socket.IO will multiplex all those connections on a single
  // physical channel. If you don't care about multiple channels, you
  // can set the namespace to an empty string.

  var initiatives = [];
  var character_icons = {};
  var turn_index = null;
  var site_name = $('#site_name').text();
  var room_id = $('#room_id').text();


  // TODO: Replacing the form does not work
  // var initiative_form = $('#initiative-wrapper').html();
  var checklist = `<ul id=checklist class="list-group list-group-flush">
                    <li class="list-group-item">
                      <div class="custom-control custom-checkbox">
                        <input type="checkbox" class="custom-control-input" id=movement_checklist>
                        <label class="custom-control-label" for=movement_checklist>Movement</label>
                      </div>
                    </li>
                    <li class="list-group-item">
                    <div class="custom-control custom-checkbox">
                        <input type="checkbox" class="custom-control-input" id=action_checklist>
                        <label class="custom-control-label" for=action_checklist>Action</label>
                      </div>
                    </li>
                    <li class="list-group-item">
                    <div class="custom-control custom-checkbox">
                        <input type="checkbox" class="custom-control-input" id=bonus_action_checklist>
                        <label class="custom-control-label" for=bonus_action_checklist>Bonus Action</label>
                      </div>
                    </li>
                  </ul>`;
  
  namespace = '/combat';
  
  // Connect to the Socket.IO server.
  // The connection URL has the following format, relative to the current page:
  //     http[s]://<domain>:<port>[/<namespace>]
  var socket = io(namespace);



  // Socketio events
  // TODO: Add room_id to all of the functions
  $('form#set_initiative').submit(function(event) {
    socket.emit('set_initiative', {character_name: $('#player_name').val(), init_val: $('#initiative_roll').val(), site_name: site_name, room_id: room_id});
    $('#initiative_roll').val(''); 
    return false;
  });

  $('form#send_chat').submit(function(event) {
    socket.emit('send_chat', {chat: $('#chat_text').val(), character_name: $('#player_name').val() || site_name, room_id: room_id});
    $('#chat_text').val(''); 
    return false;
  });
  
  $('form#start_battle').submit(function(event) {
    socket.emit('start_combat', {desc: "Start Battle", room_id: room_id});
    return false;
  });
  
  $('form#end_battle').submit(function(event) {
    socket.emit('end_combat', {desc: "End Battle", room_id: room_id});
    return false;
  });

  $('form#close_room').submit(function(event) {
    if (window.confirm("This will clear all initiative and chat data for this room and kick players. Map and character icon locations will be saved. Proceed?") ){
      socket.emit('end_room', {desc: "Close Room", room_id: room_id});
      return false;
    }
    return false; 
  });
  
  $('form#end_turn').submit(function(event) {
    var next_index = null;
    if (turn_index + 1 == initiatives.length) {
      next_index = 0;
    }
    else {
      next_index = turn_index + 1;
    }
    socket.emit('end_turn', {desc: `${initiatives[turn_index][0]}'s Turn Ended`, old_name: initiatives[turn_index][0], next_name: initiatives[next_index][0], old_site_name: initiatives[turn_index][2], next_site_name: initiatives[next_index][2], room_id: room_id});
    return false;
  });

  $('form#add_character').submit(function(event) {
    socket.emit('add_character', {char_name: $('#character_name').val(), site_name: site_name, room_id: room_id});
    return false;
  });

  socket.on('connect', function() {
    socket.emit('on_join', {room_id: room_id});
  });

  socket.on('joined', function(msg) {
    // socket.emit('join_actions', {room_id: room_id, character_name: $('#player_name').val() || ""});
    socket.emit('join_actions', {room_id: room_id, character_name: ""});
    // socket.emit('set_initiative', {character_name: $('#player_name').val() || "", init_val: $('#initiative_roll').val() || "", site_name: site_name, room_id: room_id});
    socket.emit('join_actions', {room_id: room_id, character_name: $('#player_name').val() || ""});
    socket.emit('set_initiative', {character_name: $('#player_name').val() || "", init_val: $('#initiative_roll').val() || "", site_name: site_name, room_id: room_id});
    socket.emit('character_icon_add_database', {desc: "Initialize", character_name: $('#player_name').val() || "", height: '2em', width: '2em', top: '25px', left: '25px', room_id: room_id});
  });

  socket.on('log_update', function(msg) {
    $('#log').append($('<div/>').text(msg.desc).html() + '<br>');
  });

  socket.on('initiative_update', function(msg) {
    var updated = false;

    for (i = 0; i < initiatives.length; i++) {
      if (initiatives[i][0] == msg.character_name && initiatives[i][2] == msg.site_name) {
        initiatives[i][1] = msg.init_val;
        updated = true;
      }
    }

    if (!updated) {
      initiatives.push([msg.character_name, msg.init_val, msg.site_name]);
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
    var first_turn_name = msg.first_turn_name.split(" ").join("_");
    turn_index = 0;

    // $('#initiative-wrapper').html(checklist);

    $('#log').append($('<div/>').text(msg.desc).html() + '<br>');
    $(`#${first_turn_name}-${msg.site_name}-row`).addClass("bg-warning");

    $('#set_initiative_button').prop('disabled', true);
    $('#start_battle_button').prop('disabled', true);
    $('#end_battle_button').prop('disabled', false);
    $('#add_character_button').prop('disabled', true);

    if (site_name == msg.site_name) {
      $('#end_turn_button').prop('disabled', false);
      $('#checklist_div').html(checklist);
    }
  });

  socket.on('combat_ended', function(msg) {
    var current_turn_name = msg.current_turn_name.split(" ").join("_");

    // $('#initiative-wrapper').html(initiative_form);
    $('#checklist_div').html("");

    $('#log').append($('<div/>').text(msg.desc).html() + '<br>');
    $(`#${current_turn_name}-${msg.site_name}-row`).removeClass("bg-warning");

    $('#end_turn_button').prop('disabled', true);
    $('#set_initiative_button').prop('disabled', false);
    $('#start_battle_button').prop('disabled', false);
    $('#end_battle_button').prop('disabled', true);

    if ($('#character_name option').length != 0) {
      $('#add_character_button').prop('disabled', false);
    }
  });

  socket.on('room_ended', function(msg) {
    window.location.replace("/home");
  });

  socket.on('turn_ended', function(msg) {
    // TODO: Fix having to hit "end turn" twice when characters have the same name.
    // I think its something to do with the way that the front end sorts the initiatives list
    var next_index = null;
    if (turn_index + 1 == initiatives.length) {
      next_index = 0;
    }
    else {
      next_index = turn_index + 1;
    }
    var old_id = initiatives[turn_index][0].split(" ").join("_");
    var next_id = initiatives[next_index][0].split(" ").join("_");
    turn_index = next_index;

    // $('#initiative_wrapper').html(checklist);
    $('#checklist_div').html("");

    $(`#${old_id}-${msg.old_site_name}-row`).removeClass("bg-warning");
    $(`#${next_id}-${msg.next_site_name}-row`).addClass("bg-warning");

    $('#end_turn_button').prop('disabled', true);
    if (site_name == msg.next_site_name) {
      $('#end_turn_button').prop('disabled', false);
      $('#checklist_div').html(checklist);
    }

    $('#log').append($('<div/>').text(msg.desc).html() + '<br>');
  });

  socket.on('combat_connect', function(msg) {
    var first_turn_name = msg.first_turn_name.split(" ").join("_");
    turn_index = initiatives.findIndex(x => x[0]===first_turn_name && x[2]===msg.site_name);

    // $('#initiative-wrapper').html(checklist);

    $('#log').append($('<div/>').text(msg.desc).html() + '<br>');
    $(`#${first_turn_name}-${msg.site_name}-row`).addClass("bg-warning");

    $('#set_initiative_button').prop('disabled', true);
    $('#start_battle_button').prop('disabled', true);
    $('#end_battle_button').prop('disabled', false);
    $('#add_character_button').prop('disabled', true);

    if (site_name == msg.site_name) {
      $('#end_turn_button').prop('disabled', false);
      $('#checklist_div').html(checklist);
    }
    setTimeout(() => $(`#${first_turn_name}-${msg.site_name}-row`).addClass("bg-warning"), 100);
  });

  socket.on('added_character', function(msg) {
    var char_name = msg.char_name;
    var id_char_name = char_name.split(" ").join("_") + "-init-update";
    var old_char_name = char_name.split(" ").join("_") + "-add-row";
    $('#init_placeholder').remove();
    $('#player_name').append(`<option id=${id_char_name}>${char_name}</option>`);
    $(`#${old_char_name}`).remove();
    $('#set_initiative_button').prop('disabled', false);

    if ($('#character_name option').length == 0) {
      $('#character_name').append("<option>All Characters are in the Battle!</option>");
      $('#add_character_button').prop('disabled', true);
    }
  });

  // socket.on('add_character_icon', function(msg){
  //   initial_height = "2em";
  //   initial_width = "2em";
  //   initial_top = "25px";
  //   initial_left = "25px";
  //   let character_icon_wrapper = build_html_for_character_icon(msg.character_name, msg.site_name, msg.character_image, initial_height, initial_width, initial_top, initial_left);
  //   document.getElementById("battle_map_container").appendChild(character_icon_wrapper);
  //   character_icons[msg.character_name + '_' + msg.site_name] = {'character_name': msg.character_name, 'site_name': msg.site_name, 'character_image': msg.character_image, 'height': initial_height, 'width': initial_width, 'top': initial_top, 'left': initial_left}
  //   socket.emit('character_icon_update_database', {desc: "Initialize", character_image: msg.character_image, site_name: msg.site_name, character_name: msg.character_name, height: initial_height, width: initial_width, top: initial_top, left: initial_left, room_id: room_id});
  // });

  socket.on('character_icon_update', function(msg) {
    let character_id = msg.character_name + '_' + msg.site_name;

    let html_character_icons = [];
    character_icons[character_id] = {'character_name': msg.character_name, 'site_name': msg.site_name, 'character_image': msg.character_image, 'height': msg.height, 'width': msg.width, 'top': msg.top, 'left': msg.left};
    let i = 0;
    for (let id in character_icons) {
      reloadDraggable(socket);
      reloadDroppable(socket, character_icons[id], room_id);
      reloadResizable(socket, character_icons[id], room_id);

      html_character_icons.push(build_html_for_character_icon(id, character_icons[id]['character_image'], character_icons[id]['height'], character_icons[id]['width'], character_icons[id]['top'], character_icons[id]['left']));
      
      $("#" + id).remove();
      $('#battle_map_container').append(html_character_icons[i].outerHTML);

      reloadDraggable(socket);
      reloadDroppable(socket, character_icons[id], room_id);
      reloadResizable(socket, character_icons[id], room_id);

      i++;

    }

    // This if statement is activated if there is no element with the id "#{character_id}"
    if (!$("#" + character_id).length) {
      $("#" + character_id).remove();
      $('#battle_map_container').append(build_html_for_character_icon(character_id, msg.character_image, msg.height, msg.width, msg.top, msg.left).outerHTML);
      socket.emit('character_icon_update_database', {desc: "Initialize", character_image: msg.character_image, site_name: msg.site_name, character_name: msg.character_name, height: msg.height, width: msg.width, top: msg.top, left: msg.left, room_id: room_id});
      
    }

 });
  
  // "Helper" functions
  function update_init_table() {
    code = "<tbody>";
    for (i = 0; i < initiatives.length; i++) {
      // TODO: Fix id to work when site_name has a space in it
      var id = initiatives[i][0].split(" ").join("_");
      code += `<tr id=${id}-${initiatives[i][2]}-row><td>${initiatives[i][0]}</td><td>${initiatives[i][1]}</td></tr>`;
    }
  
    code += "</tbody>";
  
    return code;
  }

  function build_html_for_character_icon(character_id, character_image, height, width, top, left) {
    let character_icon_wrapper = document.createElement("div");
    character_icon_wrapper.setAttribute("id", character_id);
    character_icon_wrapper.setAttribute("class", "characterIconWrapper draggable ui-draggable ui-draggable-handle");
    character_icon_wrapper.setAttribute("style", "position:absolute; z-index:10; top:" + top + "; left:" + left + "; display:inline-block;");

    let character_icon = document.createElement("img");
    character_icon.setAttribute("id", "characterIcon");
    character_icon.setAttribute("class", "characterIcon resizable ui-resizable");
    character_icon.setAttribute("style", "position: static; height: " + height + "; width: " + width + "; z-index: 10; margin: 0px; resize: none; zoom: 1; display: block; draggable: true;");
    character_icon.setAttribute("src", character_image);

    character_icon_wrapper.appendChild(character_icon);
    return character_icon_wrapper;
  }
});


function compareSecondColumn(a, b) {
  if (a[1] === b[1]) {
      return 0;
  }
  else {
      return (a[1] > b[1]) ? -1 : 1;
  }
  //https://stackoverflow.com/questions/16096872/how-to-sort-2-dimensional-array-by-column-value
}

function reloadDraggable(socket){
  $(".draggable").draggable({
    containment: 'parent',
    stack: ".characterIcon",
    zIndex: 100
  });

// https://api.jqueryui.com/draggable
}


function reloadDroppable(socket, character_icon_data, room_id){
  $(".droppable").droppable({
    accept: ".draggable",
    drop: function(event, ui) {
      // TODO: Log character icon postion when dropped
      new_top = ui.position.top;
      new_left = ui.position.left;
      socket.emit('character_icon_update_database', {desc: "ChangeLocation", character_image: character_icon_data['character_image'], site_name: character_icon_data['site_name'], character_name: character_icon_data['character_name'], new_top: new_top, new_left: new_left, room_id: room_id});
    }
  });

// https://api.jqueryui.com/droppable
}

function reloadResizable(socket, character_icon_data, room_id) {
  $(".resizable" ).resizable({
    autoHide: true,
    ghost: true,
    // get size of battle map and then set max size for resizing to that
    maxHeight: 300,
    maxWidth: 300,
    minHeight: 25,
    minWidth: 25,
    stop: function( event, ui ) {
      // TODO: Log chracter icon size when done resizing in json positions file
      new_width = ui.size.width;
      new_height = ui.size.height;
      socket.emit('character_icon_update_database', {desc: "Resize", character_image: character_icon_data['character_image'], site_name: character_icon_data['site_name'], character_name: character_icon_data['character_name'], new_width: new_width, new_height: new_height, room_id: room_id});
    }
  });

// https://api.jqueryui.com/resizable/
}

// function TestHTMLUpdate() {
//   $('#battle_map_container').html('<img id="battle_map" style="height:100%;width:100%;" draggable="false" src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Flag_of_Libya_%281977%E2%80%932011%29.svg/300px-Flag_of_Libya_%281977%E2%80%932011%29.svg.png">');
//   $('#initiative-table').html('<tbody><tr id=Helga-Yee-row><td>Helga</td><td>4444</td></tr></tbody>');
// }



// TODO: combine add_character_icon and character_icon_update
// TODO: Standardize naming conventions for functions and variables