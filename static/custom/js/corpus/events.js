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
    $entity_root.addClass('custom-auto-complete');
    $relation_source.addClass('custom-auto-complete');
    $relation_target.addClass('custom-auto-complete');
    $action_actor.addClass('custom-auto-complete');
    $('.custom-auto-complete').autoComplete({
        events: {
            searchPost: function (server_results) {
                var current_roots = $corpus_table.data('current_roots');
                return [...current_roots, ...server_results];
            }
        }
    });
});

$corpus_table.on('check.bs.table', function (e, row, $element, field) {
    $corpus_table.bootstrapTable('collapseAllRows');
    $corpus_table.bootstrapTable('expandRow', $element.data('index'));
});

$corpus_table.on('expand-row.bs.table', function (e, index, row, $detail) {
    $line_id_entity.val(row.line_id);
    $line_id_relation.val(row.line_id);
    $line_id_action.val(row.line_id);
    $entity_root.val("");
    $relation_source.val("");
    $relation_target.val("");
    $relation_detail.val("");
    $action_actor.val("");

    var row_roots = new Set();
    $.each(row.analysis, function(index, word) {
        if (word.is_noun) {
            row_roots.add(word.root);
        }
    });
    $corpus_table.data('current_roots', row_roots);

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
            entity_html = entity_formatter(entity.root, entity.type, "", entity.annotator);
            entity_list_html.push(entity_html);
        }
    });

    $.each(row.relation, function (index, relation) {
        if (!relation.is_deleted) {
            relation_html = relation_formatter(relation.source, relation.label, relation.target, relation.detail, "", relation.annotator);
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
            entity_html = entity_formatter(entity.root, entity.type, "list-group-item-warning", entity.annotator);
            entity_list_html.push(entity_html);
        });
    }
    if (unconfirmed_relations !== null) {
        $.each(JSON.parse(unconfirmed_relations), function (index, relation) {
            relation_html = relation_formatter(relation.source, relation.label, relation.target, relation.detail, "list-group-item-warning", relation.annotator);
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
