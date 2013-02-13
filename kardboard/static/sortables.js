$(function() {
    $( "td.cards_backlog" ).sortable({
        items: "div.card_on_board:not(.ui-state-disabled)",
        cursor: "move",
        revert: true,
        axis: "y"
    });

    $( "td.cards_backlog" ).disableSelection();

    $( "td.cards_backlog" ).sortable( "disable" ); // Disable by default

    var fixHelper = function(e, ui) {
        ui.children().each(function() {
            $(this).width($(this).width());
        });
        return ui;
    };

    $( "tbody.sortable_table" ).sortable({
        cursor: "move",
        revert: true,
        axis: "y",
        handle: ".reorder",
        helper: fixHelper,
        forceHelperSize: true,
        forcePlaceholderSize: true,
    });

    $( "tbody.sortable_table" ).disableSelection();

    $( "tbody.sortable_table" ).sortable( "disable" ); // Disable by default
});