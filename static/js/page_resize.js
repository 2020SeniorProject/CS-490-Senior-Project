$(document).ready(function() {
    resize_body();
});

$(window).resize(function() {
    resize_body();
});

function resize_body() {
    var navbarHeightStr = $("#main_navbar").css("height");
    var navbarHeight = parseFloat(navbarHeightStr);
    var windowSize = window.innerHeight;

    $("#content").css("margin-top", navbarHeight + 10);
    $("#content").css("height", windowSize - navbarHeight - 20);

    if ($("#start_battle_button").length == 1) {
        var parentHeight = $("#row1_col3").outerHeight(true);

        var title = $("#dm_tools").outerHeight(true);
        var startBattle = $("#start_battle").outerHeight(true);
        var endBattle = $("#end_battle").outerHeight(true);
        var endRoom = $("#close_room").outerHeight(true);
        var logTitle = $("#log_title").outerHeight(true);

        let totalHeight = title + startBattle + endBattle + endRoom + logTitle;

        $("#log_div").css("height", parentHeight - totalHeight - 10);
    }
}