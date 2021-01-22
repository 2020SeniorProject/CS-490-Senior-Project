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

    console.log("resize done");
}