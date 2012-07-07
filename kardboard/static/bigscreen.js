function toggle_bigscreen() {
    if(screen.width == window.outerWidth && screen.height == window.outerHeight) {
        $("body").toggleClass("bigscreen", true);
    }
    else {
        $("body").toggleClass("bigscreen", false);
    }

}

$(window).resize(toggle_bigscreen)

$(document).ready(toggle_bigscreen)

