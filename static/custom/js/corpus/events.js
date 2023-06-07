// Globals
// var all_roots = new Set();

// Event Handlers
// $corpus_table.on('load-success.bs.table', function (e, data, status, xhr) {
//    // load all the added roots
//     all_roots.clear();
//     for (row of data) {
//         for (entity of row.entity) {
//             all_roots.add("<option>" + entity.root + "</option>");
//         }
//     }
// });

$(document).ready(function () {
    // Activate Auto-Complete Suggestions
    $entity_root.addClass('custom-auto-complete');
    $relation_source.addClass('custom-auto-complete');
    $relation_target.addClass('custom-auto-complete');
    $relation_detail.addClass('custom-auto-complete');
    // $action_actor.addClass('custom-auto-complete');
    $('.custom-auto-complete').autoComplete();
    // $('.custom-auto-complete').autoComplete({
    //     events: {
    //         searchPost: function (server_results) {
    //             var current_roots = $corpus_table.data('current_roots');
    //             return [...current_roots, ...server_results];
    //         }
    //     }
    // });

    // Split Columns
    const splitobj = Split(["#corpus-column", "#annotation-column"], {
        elementStyle: function (dimension, size, gutterSize) {
            $(window).trigger('resize');
            return {
                'flex-basis': `calc(${size}% - ${gutterSize}px)`
            };
        },
        gutterStyle: function (dimension, gutterSize) {
            return {
                'flex-basis': `${gutterSize}px`
            };
        },
        sizes: [70, 30],
        minSize: 300,
        gutterSize: 10,
        cursor: 'col-resize'
    });

});

// Expand Row on Select
$corpus_table.on('check.bs.table', function (e, row, $element, field) {
    $corpus_table.bootstrapTable('collapseAllRows');
    $corpus_table.bootstrapTable('expandRow', $element.data('index'));
});

// Row Expand
$corpus_table.on('expand-row.bs.table', function (e, index, row, $detail) {
    const unique_id = row.line_id;
    $line_id_entity.val(unique_id);
    $line_id_relation.val(unique_id);

    const $active_tab = $('.annotation-tab[aria-selected="true"]');
    const tab_id = $active_tab.attr("id");

    if (tab_id == "entity-tab") {
        setup_entity_annotation(unique_id);
    }
    if (tab_id == "relation-tab") {
        setup_relation_annotation(unique_id);
    }
    // if (tab_id == "action-tab") {
    //     setup_action_annotation(unique_id);
    // }
});

// Tab Change
$('.annotation-tab[data-toggle="pill"]').on('shown.bs.tab', function (event) {
    const $active_tab = $(event.target);
    const tab_id = $active_tab.attr("id");

    if (tab_id == "entity-tab") {
        const unique_id = $line_id_entity.val();
        if (unique_id == "") {
            $.notify({
                message: "Please select a row first."
            }, {
                type: "warning"
            })
            return;
        }
        setup_entity_annotation(unique_id);
    }

    if (tab_id == "relation-tab") {
        const unique_id = $line_id_relation.val();
        if (unique_id == "") {
            $.notify({
                message: "Please select a row first."
            }, {
                type: "warning"
            })
            return;
        }
        setup_relation_annotation(unique_id);
    }

    // if (tab_id == "action-tab") {
    //     const unique_id = $line_id_action.val();
    //     if (unique_id == "") {
    //         $.notify({
    //             message: "Please select a row first."
    //         }, {
    //             type: "warning"
    //         })
    //         return;
    //     }
    //     setup_action_annotation(unique_id);
    // }
});

// Page Change
$corpus_table.on('page-change.bs.table', function (e, number, size) {
    $line_id_entity.val("");
    $line_id_relation.val("");
    // $line_id_action.val("");

    $entity_root.val("");
    $entity_type.val("");
    $entity_type.selectpicker('refresh');
    $entity_list.html("");

    $relation_source.val("");
    $relation_target.val("");
    $relation_label.val("");
    $relation_label.selectpicker('refresh');
    $relation_detail.val("");
    $relation_list.html("")

    // $action_label.selectpicker('refresh');
    // $action_actor_label.selectpicker('refresh');
    // $action_actor.val("");
    // $action_list.html("");
});

// Click / Double-Click Cell
// 'click-cell.bs.table' / 'dbl-click-cell.bs.table'
$corpus_table.on('dbl-click-cell.bs.table', function (event, field, value, row, $element) {

});