/*jshint esversion: 6 */


$(document).ready(function() {
  jQuery.browser = {
    msie: false,
    version: 0
  };

  // Use a "/test" namespace.
  // An application can open a connection on multiple namespaces, and
  // Socket.IO will multiplex all those connections on a single
  // physical channel. If you don't care about multiple channels, you
  // can set the namespace to an empty string.

  var initiatives = [];
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


  // javascript events
  // TODO: Add room_id to all of the functions
  $('form#set_initiative').submit(function(event) {
    socket.emit('set_initiative', {character_name: $('#player_name').val(), init_val: $('#initiative_roll').val(), site_name: site_name, room_id: room_id});
    $('#initiative_roll').val(''); 
    return false;
  });

  $('form#send_chat').submit(function(event) {
    if ($('#chat_text').val().trim().length != 0) {
      socket.emit('send_chat', {chat: $('#chat_text').val(), character_name: site_name, room_id: room_id});
      $('#chat_text').val(''); 
    }
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
    socket.emit('end_turn', {desc: `${initiatives[turn_index][0]}'s Turn Ended`, previous_character_name: initiatives[turn_index][0], next_character_name: initiatives[next_index][0], previous_site_name: initiatives[turn_index][2], next_site_name: initiatives[next_index][2], room_id: room_id});
    return false;
  });

  $('form#add_character').submit(function(event) {
    socket.emit('add_character', {char_name: $('#character_name').val(), site_name: site_name, room_id: room_id});
    return false;
  });

  $('form#add_npc').submit(function(event) {
    socket.emit('add_npc', {site_name: site_name, room_id: room_id});
    return false;
  });

  // socket.io events
  socket.on('connect', function() {
    socket.emit('on_join', {room_id: room_id});
  });

  socket.on('joined', function(msg) {
    socket.emit('join_actions', {room_id: room_id, character_name: ""});
  });

  socket.on('log_update', function(msg) {
    var log = $('<div/>').text(msg.desc);
    var col = $('<div/>').addClass("col");
    var row = $('<div/>').addClass("row");
    col.append(log);
    row.append(col);
    $('#log').append(row);
    $('#log_div').animate({ scrollTop: $('#log_div').prop("scrollHeight")}, 10);
  });

  // TODO: allow characters to select who goes first when initiatives tied
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
    var log = $('<div/>').text(`${msg.character_name}: ${msg.chat}`);
    var col = $('<div/>').addClass("col");
    var row = $('<div/>').addClass("row");
    col.append(log);
    row.append(col);
    // var name = $('<p/>').text(`${msg.character_name}: ${msg.chat}`).addClass("mb-0 mt-0");
    // var chat;

    // var chat = $('<p/>').text(`${msg.chat}`).addClass("mb-0 mt-0");
    // // console.log(chat.width());
    // // console.log($('#col1').css("max-width"));
    // // if ($('#col1').css("max-width") == "100%") {
    // //   ($('#col1').css("max-width", )
    // // }
    // $('#col1').append(name);    
    // $('#col2').append(chat);
    $('#chat-list').append(row);
    $('#chat-box').animate({ scrollTop: $('#chat-box').prop("scrollHeight")}, 10);
  });

  socket.on('lockout_spammer', function(msg) {
    $('#send_chat_button').prop('disabled', true);
    $('#chat_text').val(msg.message);
    let timeout =  msg.spam_penalty * 1000;
    setTimeout(function() {
      $('#send_chat_button').prop('disabled', false);
      $('#chat_text').val('');
    }, timeout);
  });

  socket.on('combat_started', function(msg) {
    var first_turn_name = msg.first_turn_name.split(" ").join("_");
    turn_index = 0;

    // $('#initiative-wrapper').html(checklist);

    $(`#${first_turn_name}-${msg.site_name}-row`).addClass("bg-warning");

    let token_id_to_highlight = first_turn_name + "_" + msg.site_name;
    $(`#${token_id_to_highlight}`).find("img").css( "border", "3px solid red" );

    $('#set_initiative_button').prop('disabled', true);
    $('#start_battle_button').prop('disabled', true);
    $('#end_battle_button').prop('disabled', false);
    $('#add_character_button').prop('disabled', true);
    $('#add_npc_button').prop('disabled', true);

    if (site_name == msg.site_name) {
      $('#end_turn_button').prop('disabled', false);
      $('#checklist_div').html(checklist);
    }
  });

  socket.on('combat_ended', function(msg) {
    var current_turn_name = msg.current_turn_name.split(" ").join("_");

    // $('#initiative-wrapper').html(initiative_form);
    $('#checklist_div').html("");

    $(`#${current_turn_name}-${msg.site_name}-row`).removeClass("bg-warning");

    $('#end_turn_button').prop('disabled', true);
    $('#set_initiative_button').prop('disabled', false);
    $('#start_battle_button').prop('disabled', false);
    $('#end_battle_button').prop('disabled', true);

    let token_id_to_unhighlight = current_turn_name + "_" + msg.site_name;
    $(`#${token_id_to_unhighlight}`).find("img").css( "border", "0px" ); // Try empty string instead of "0px"

    if ($('#character_name option').length != 0) {
      $('#add_character_button').prop('disabled', false);
      $('#add_npc_button').prop('disabled', false);
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
    var previous_character_name = initiatives[turn_index][0].split(" ").join("_");
    var next_character_name = initiatives[next_index][0].split(" ").join("_");
    turn_index = next_index;

    // $('#initiative_wrapper').html(checklist);
    $('#checklist_div').html("");

    $(`#${previous_character_name}-${msg.previous_site_name}-row`).removeClass("bg-warning");
    $(`#${next_character_name}-${msg.next_site_name}-row`).addClass("bg-warning");

    let token_id_to_highlight = next_character_name + "_" + msg.next_site_name;
    $(`#${token_id_to_highlight}`).find("img").css( "border", "3px solid red" );

    let token_id_to_unhighlight = previous_character_name + "_" + msg.previous_site_name;
    $(`#${token_id_to_unhighlight}`).find("img").css( "border", "0px" ); // Try empty string instead of "0px"

    $('#end_turn_button').prop('disabled', true);
    if (site_name == msg.next_site_name) {
      $('#end_turn_button').prop('disabled', false);
      $('#checklist_div').html(checklist);
    }
  });

  socket.on('combat_connect', function(msg) {
    var first_turn_name = msg.first_turn_name.split(" ").join("_");
    turn_index = initiatives.findIndex(x => x[0]===first_turn_name && x[2]===msg.site_name);

    // $('#initiative-wrapper').html(checklist);
    // TODO: highlight current character's icon here

    $(`#${first_turn_name}-${msg.site_name}-row`).addClass("bg-warning");

    $('#set_initiative_button').prop('disabled', true);
    $('#start_battle_button').prop('disabled', true);
    $('#end_battle_button').prop('disabled', false);
    $('#add_character_button').prop('disabled', true);
    $('#add_npc_button').prop('disabled', true);

    if (site_name == msg.site_name) {
      $('#end_turn_button').prop('disabled', false);
      $('#checklist_div').html(checklist);
    }
    setTimeout(() => $(`#${first_turn_name}-${msg.site_name}-row`).addClass("bg-warning"), 100);
  });

  socket.on('populate_select_with_character_names', function(msg) {
    if (msg.site_name == site_name) {
      let character_name = msg.character_name;
      let id_character_name = character_name.split(" ").join(":") + "-init-update";
      let old_character_name = character_name.split(" ").join("\\:") + "-add-row";
      $('#init_placeholder').remove();
      $('#player_name').append(`<option id=${id_character_name}>${character_name}</option>`);
      $(`#${old_character_name}`).remove();
      $('#set_initiative_button').prop('disabled', false);

      if ($('#character_name option').length == 0) {
        $('#character_name').append("<option>All Characters are in the Battle!</option>");
        $('#add_character_button').prop('disabled', true);
      }
    }
  });

 socket.on('redraw_character_tokens_on_map', function(msg) {
  for (let character in msg) {
    let character_site_name = msg[character].site_name;
    let character_name = msg[character].character_name.split(" ").join(":");
    let character_image = msg[character].character_image;
    let room_id = msg[character].room_id;
    let height = msg[character].height;
    let width = msg[character].width;
    let top = msg[character].top;
    let left = msg[character].left;
    let is_turn = msg[character].is_turn;

    let character_html_id_build = character_name + "_" + character_site_name;

    let character_token_html = build_html_for_character_icon(character_html_id_build, character_image, height, width, top, left, is_turn);

    let character_html_id_remove = character_name.split(":").join("\\:") + "_" + character_site_name;

    $("#" + character_html_id_remove).remove();
    $('#battle_map_container').append(character_token_html.outerHTML);

    reloadDraggable(socket);
    reloadDroppable(socket, room_id);
    reloadResizable(socket, room_id);
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

  function build_html_for_character_icon(character_id, character_image, height, width, top, left, is_turn) {
    let character_icon_wrapper = document.createElement("div");
    character_icon_wrapper.setAttribute("id", character_id);
    character_icon_wrapper.setAttribute("class", "characterIconWrapper draggable ui-draggable ui-draggable-handle");
    character_icon_wrapper.setAttribute("style", "position:absolute; z-index:10; top:" + top + "; left:" + left + "; height: " + height + "; width: " + width + "; display:inline-block;");

    let character_icon = document.createElement("img");
    character_icon.setAttribute("id", "characterIcon");
    character_icon.setAttribute("class", "characterIcon resizable ui-resizable");
    if (is_turn) {
      character_icon.setAttribute("style", "position: static; height: 100%; width: 100%; z-index: 10; margin: 0px; resize: none; zoom: 1; display: block; draggable: true; border: 3px solid red");
    }
    else {
      character_icon.setAttribute("style", "position: static; height: 100%; width: 100%; z-index: 10; margin: 0px; resize: none; zoom: 1; display: block; draggable: true;");
    }
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


function scrapeCharacterImage(partially_sliced_character_image) {
  let equal_images = (partially_sliced_character_image.substring(0, partially_sliced_character_image.indexOf('"')) === partially_sliced_character_image.substring(0, partially_sliced_character_image.indexOf("\"")));
  if (! equal_images) {
    if (partially_sliced_character_image.substring(0, partially_sliced_character_image.indexOf('"')).length() < partially_sliced_character_image.substring(0, partially_sliced_character_image.indexOf("\"")).length()){
      let character_image = partially_sliced_character_image.substring(0, partially_sliced_character_image.indexOf('"'));
      return character_image;
    }
  }
  else {
    let character_image = partially_sliced_character_image.substring(0, partially_sliced_character_image.indexOf("\""));
    return character_image;
  }
  return "https://upload.wikimedia.org/wikipedia/commons/6/6a/Broken-image-389560.svg";
}


function reloadDraggable(socket){
  $(".draggable").draggable({
    containment: 'parent',
    stack: ".characterIcon",
    zIndex: 100
  });

// https://api.jqueryui.com/draggable
}


function reloadDroppable(socket, room_id){
  $(".droppable").droppable({
    accept: ".draggable",
    drop: function(event, ui) {
      let parent_width = $("#"+ui.draggable[0].id).parent().width();
      let parent_height = $("#"+ui.draggable[0].id).parent().height();
      let new_top = (ui.position.top / parent_height)*100 + "%";
      let new_left = (ui.position.left / parent_width)*100 + "%";
      let site_name = ui.draggable[0].id.split("_")[1];
      let character_name = ui.draggable[0].id.split("_")[0].split(":").join(" ");
      let partially_sliced_character_image = ui.draggable[0].innerHTML.substring(ui.draggable[0].innerHTML.indexOf("src") + 5);
      let character_image = scrapeCharacterImage(partially_sliced_character_image);
      if (ui.draggable[0].innerHTML.substring(ui.draggable[0].innerHTML.indexOf("border:"), ui.draggable[0].innerHTML.indexOf("border:") + 21) == "border: 3px solid red") {
        var is_turn = 1;
        socket.emit('character_icon_update_database', {desc: "ChangeLocation", character_image: character_image, site_name: site_name, character_name: character_name, new_top: new_top, new_left: new_left, new_width: "Null", new_height: "Null", is_turn: is_turn, room_id: room_id});
        character_image = "";
      }
      else {
        var is_turn = 0;
        socket.emit('character_icon_update_database', {desc: "ChangeLocation", character_image: character_image, site_name: site_name, character_name: character_name, new_top: new_top, new_left: new_left, new_width: "Null", new_height: "Null", is_turn: is_turn, room_id: room_id});
        character_image = "";
      }
    }
  });

// https://api.jqueryui.com/droppable
}


function reloadResizable(socket, room_id) {
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
      let min_height_ratio = 0.015;
      let min_width_ratio = 0.015;
      let max_height_ratio = 0.3;
      let max_width_ratio = 0.3;
      let parent_width = $("#"+ui.originalElement[0].offsetParent.id).parent().width();
      let parent_height = $("#"+ui.originalElement[0].offsetParent.id).parent().height();
      // let height = $("#"+ui.originalElement[0].offsetParent.id).height();
      // let width = $("#"+ui.originalElement[0].offsetParent.id).width();
      let height = ui.size.height;
      let width = ui.size.width;
      let height_ratio = height/parent_height;
      let width_ratio = width/parent_width;
      if (height_ratio > max_height_ratio){
        height_ratio = max_height_ratio;
      }
      if (height_ratio < min_height_ratio){
        height_ratio = min_height_ratio;
      }
      if (width_ratio > max_width_ratio){
        width_ratio = max_width_ratio;
      }
      if (width_ratio < min_width_ratio){
        width_ratio = min_width_ratio;
      }
      let new_height = height_ratio*100 + "%";
      let new_width = width_ratio*100 + "%";
      // let new_width = ui.size.width.toString() + "px";
      // let new_height = ui.size.height.toString() + "px";
      let site_name = ui.originalElement[0].offsetParent.id.split("_")[1];
      let character_name = ui.originalElement[0].offsetParent.id.split("_")[0].split(":").join(" ");
      let character_image = ui.originalElement[0].src;
      if (ui.originalElement[0].outerHTML.substring(ui.originalElement[0].outerHTML.indexOf("border:"), ui.originalElement[0].outerHTML.indexOf("border:") + 21) == "border: 3px solid red") {
        var is_turn = 1;
        socket.emit('character_icon_update_database', {desc: "Resize", character_image: character_image, site_name: site_name, character_name: character_name, new_top: "Null", new_left: "Null", new_width: new_width, new_height: new_height, is_turn: is_turn, room_id: room_id});
      }
      else {
        var is_turn = 0;
        socket.emit('character_icon_update_database', {desc: "Resize", character_image: character_image, site_name: site_name, character_name: character_name, new_top: "Null", new_left: "Null", new_width: new_width, new_height: new_height, is_turn: is_turn, room_id: room_id});
      }
    }
  });

// https://api.jqueryui.com/resizable/
}


// function TestHTMLUpdate() {
//   $('#battle_map_container').html('<img id="battle_map" style="height:100%;width:100%;" draggable="false" src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Flag_of_Libya_%281977%E2%80%932011%29.svg/300px-Flag_of_Libya_%281977%E2%80%932011%29.svg.png">');
//   $('#initiative-table').html('<tbody><tr id=Helga-Yee-row><td>Helga</td><td>4444</td></tr></tbody>');
// }