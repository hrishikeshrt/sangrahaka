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
    $action_actor.addClass('custom-auto-complete');
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
    var splitobj = Split(["#corpus-column","#annotation-column"], {
        elementStyle: function (dimension, size, gutterSize) {
            $(window).trigger('resize');
            return {
                'flex-basis': `calc(${size}% - ${gutterSize}px)`
            };
        },
        gutterStyle: function (dimension, gutterSize) {
            return {
                'flex-basis':  `${gutterSize}px`
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
    $line_id_entity.val(row.line_id);
    $line_id_relation.val(row.line_id);
    $line_id_action.val(row.line_id);
    $entity_root.val("");
    $relation_source.val("");
    $relation_target.val("");
    $relation_detail.val("");
    $action_actor.val("");

    // var row_roots = new Set();
    // $.each(row.analysis, function(index, word) {
    //     if (word.is_noun) {
    //         row_roots.add(word.root);
    //     }
    // });
    // $corpus_table.data('current_roots', row_roots);

    // var suggest_roots = new Set([...row_roots, ...all_roots]);

    // $datalist_root.html("");
    // $datalist_root.append(Array.from(suggest_roots).join(""));

    // $datalist_source.html("");
    // $datalist_source.append(Array.from(suggest_roots).join(""));
    // $datalist_target.html("");
    // $datalist_target.append(Array.from(suggest_roots).join(""));

    var entity_list_html = [];
    var relation_list_html = [];
    var action_list_html = [];

    $.each(row.entity, function (index, entity) {
        if (!entity.is_deleted) {
            entity_html = entity_formatter({
                "id": entity.id,
                "lemma": entity.lemma,
                "label": entity.label,
                "annotator": entity.annotator
            }, "");
            entity_list_html.push(entity_html);
        }
        attach_context_menu(".context-node", [
            {
                header: "Node Actions",
            },
            {
                text: "<i class='fa fa-info-circle mr-1'></i> Information",
                action: function(e) {
                    e.preventDefault();
                    alert("I will show information about the node.");
                },
                disabled: true
            },
            {
                text: "<i class='fa fa-edit mr-1'></i> Edit Entity Text",
                action: function(e) {
                   e.preventDefault();
                   alert("I will launch a modal to edit entity text.");
                },
            },
            {
                text: "<i class='fa fa-edit mr-1'></i> Change Entity Type",
                action: function(e) {
                   e.preventDefault();
                   alert("I will launch a modal to change entity type.")
                },
                disabled: true
            }
        ]);
    });

    $.each(row.relation, function (index, relation) {
        if (!relation.is_deleted) {
            relation_html = relation_formatter({
                "id": relation.id,
                "source": relation.source,
                "label": relation.label,
                "detail": relation.detail,
                "target": relation.target,
                "annotator": relation.annotator,
            }, "");
            relation_list_html.push(relation_html);
        }
    });

    $.each(row.action, function (index, action) {
        if (!action.is_deleted) {
            action_html = action_formatter(action.label, action.actor_label, action.actor, "", action.annotator);
            action_list_html.push(action_html);
        }
    });

    var unconfirmed = storage.getItem(row.line_id);
    var unconfirmed_relations = storage.getItem(row.line_id + '_relations');
    var unconfirmed_actions = storage.getItem(row.line_id + '_actions');

    if (unconfirmed !== null) {
        $.each(JSON.parse(unconfirmed), function (index, entity) {
            entity_html = entity_formatter({
                "lemma": entity.lemma,
                "label": entity.label,
                "annotator": entity.annotator
            }, "list-group-item-warning");
            entity_list_html.push(entity_html);
        });
    }
    if (unconfirmed_relations !== null) {
        $.each(JSON.parse(unconfirmed_relations), function (index, relation) {
            relation_html = relation_formatter({
                "source": relation.source,
                "label": relation.label,
                "detail": relation.detail,
                "target": relation.target,
                "annotator": relation.annotator
            }, "list-group-item-warning");
            relation_list_html.push(relation_html);
        });
    }
    if (unconfirmed_actions !== null) {
        $.each(JSON.parse(unconfirmed_actions), function (index, action) {
            action_html = action_formatter(action.label, action.actor_label, action.actor, "list-group-item-warning", action.annotator);
            action_list_html.push(action_html);
        });
    }

    $entity_list.html("").append(entity_list_html.join(""));
    $relation_list.html("").append(relation_list_html.join(""));
    $action_list.html("").append(action_list_html.join(""));

    $('[name="entity"]').bootstrapToggle();
    $('[name="relation"]').bootstrapToggle();
    $('[name="action"]').bootstrapToggle();
});

// Page Change
$corpus_table.on('page-change.bs.table', function (e, number, size) {
    $line_id_entity.val("");
    $line_id_relation.val("");
    $line_id_action.val("");

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

    $action_label.selectpicker('refresh');
    $action_actor_label.selectpicker('refresh');
    $action_actor.val("");
    $action_list.html("");
});

// Click / Double-Click Cell
// 'click-cell.bs.table' / 'dbl-click-cell.bs.table'
$corpus_table.on('dbl-click-cell.bs.table', function (event, field, value, row, $element) {

});