function toggle_bigscreen() {
    if(screen.width == window.innerWidth && screen.height == window.innerHeight) {
        $("body").toggleClass("bigscreen", true);
    }
    else {
        $("body").toggleClass("bigscreen", false);
    }

}

$(window).resize(toggle_bigscreen)

$(document).ready(toggle_bigscreen)

