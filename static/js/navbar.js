$(document).ready(function() {
    const route = $(location).attr('pathname');
    const first_item = route.split('/')[1];

    switch(first_item) {
        case "home":
        case "play":
        case "characters":
        case "user":
            $(`#path_${first_item}`).addClass('active underline_text');
            break;
        case "room":
            $("#path_home").addClass('active underline_text');
        default:
            break;
    }
});