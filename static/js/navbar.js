// Called when the page fully loads.
// Underlines the correct page option on the navbar.
$(document).ready(function() {
    const route = $(location).attr('pathname');
    const first_item = route.split('/')[1];

    switch(first_item) {
        case "home":
        case "characters":
        case "user":
        case "rooms":
            $(`#path_${first_item}`).addClass('active underline_text');
            break;
        case "play":
        case "spectate":
            $("#path_rooms").addClass('active underline_text');
            break;
        default:
            break;
    }
});