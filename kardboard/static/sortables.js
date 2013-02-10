$(function() {
    $( "td.cards_backlog" ).sortable({
        items: "div.card_on_board:not(.ui-state-disabled)",
        cursor: "move",
        revert: true
    });

    $( "td.cards_backlog div.card_on_board" ).disableSelection();
});