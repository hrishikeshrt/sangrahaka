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
    $line_id_entity.val(row.line_id);
    $line_id_relation.val(row.line_id);
    $line_id_action.val(row.line_id);
    $entity_root.val("");
    $relation_source.val("");
    $relation_target.val("");
    $relation_detail.val("");
    $action_actor.val("");

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
            }, true);
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
            }, true);
            relation_list_html.push(relation_html);
        });
    }
    if (unconfirmed_actions !== null) {
        $.each(JSON.parse(unconfirmed_actions), function (index, action) {
            action_html = action_formatter(action.label, action.actor_label, action.actor, true, action.annotator);
            action_list_html.push(action_html);
        });
    }

    $entity_list.html("").append(entity_list_html.join(""));
    $relation_list.html("").append(relation_list_html.join(""));
    $action_list.html("").append(action_list_html.join(""));

    $('[name="entity"]').bootstrapToggle();
    $('[name="relation"]').bootstrapToggle();
    $('[name="action"]').bootstrapToggle();

    /* --------------------------------------------------------------------- */
    // Menu Items

    const node_actions_header_menu_item = {
        header: "Node Actions",
    }
    const node_information_menu_item = {
        text: "<i class='fa fa-info-circle mr-1'></i> Information",
        action: function (e, context) {
            e.preventDefault();
            const $element = $(context);
            const lemma = $element.find('div.entity-lemma').text();
            const label = $element.find('div.entity-label').text();
            const label_id = $element.data('node-label-id');
            const lexicon_id = $element.data('lexicon-id');
            const node_id = $element.data('node-id');
            const alert_text = [
                `${lemma} :: ${label}`,
                `Node ID: ${node_id}`,
                `Lemma ID: ${lexicon_id}`,
                `Label ID: ${label_id}`
            ];
            $.notify({
                message: alert_text.join("<br>")
            });
        }
    };
    const edit_node_lexicon_menu_item = {
        text: "<i class='fa fa-edit mr-1'></i> Edit Entity Text",
        action: function (e, context) {
            e.preventDefault();
            const $element = $(context);
            const current_lemma = $element.find('div.entity-lemma').text();
            $edit_lexicon_modal.modal('show');
            $edit_lexicon_current_lemma.val(current_lemma);
            $edit_lexicon_replacement_lemma.val(current_lemma);
            setTimeout(function () {
                $edit_lexicon_replacement_lemma.focus();
            }, 500);
        },
    };
    const edit_node_label_menu_item = {
        text: "<i class='fa fa-edit mr-1'></i> Change Entity Type",
        action: function (e, context) {
            e.preventDefault();
            $.notify({
                message: "Eventually this will launch a modal to change entity type."
            }, {
                type: "warning"
            });
        },
        disabled: true
    };

    /* --------------------------------------------------------------------- */

    attach_context_menu(".context-node", [
        node_actions_header_menu_item,
        node_information_menu_item,
        edit_node_lexicon_menu_item,
        edit_node_label_menu_item
    ]);
});

$edit_lexicon_submit_button.on('click', function (e) {
    $edit_lexicon_modal.modal('hide');
    if ($edit_lexicon_form[0].checkValidity()) {
        $.post(API_URL, {
                action: "update_lexicon",
                current_lemma: $edit_lexicon_current_lemma.val().trim(),
                replacement_lemma: $edit_lexicon_replacement_lemma.val().trim()
            },
            function (response) {
                $.notify({
                    message: response.message
                }, {
                    type: response.style
                });
                if (response.success) {
                    // NOTE: potential bug when there's an unconfirmed relation using an existing entity and we change the lexicon
                    // TODO: investigate and fix if required
                    const current_text = $edit_lexicon_current_lemma.val().trim();
                    const replacement_text = $edit_lexicon_replacement_lemma.val().trim();

                    // update local entity list
                    $.each($entity_list.find("div.entity-lemma"), function () {
                        // TODO: update lemma
                        const current_lemma = $(this).text();
                        if (current_lemma == current_text) {
                            $(this).text(replacement_text);
                        }
                    });
                    // update local relation list
                    $.each($relation_list.find('span.relation-lemma'), function () {
                        const current_lemma = $(this).text();
                        if (current_lemma == current_text) {
                            $(this).text(replacement_text);
                        }
                    });

                    // update local table
                    setTimeout(() => {
                        const data = $corpus_table.bootstrapTable('getData');
                        for (const row of data) {
                            for (const entity of row.entity) {
                                // iterate through current_row.entity
                                if (entity.lemma.lemma == current_text) {
                                    entity.lemma.lemma = replacement_text;
                                }
                            }
                            for (const relation of row.relation) {
                                // iterate through current_row.relation
                                if (relation.source.lemma == current_text) {
                                    relation.source.lemma = replacement_text;
                                }
                                if (relation.target.lemma == current_text) {
                                    relation.target.lemma = replacement_text;
                                }
                            }
                            $corpus_table.bootstrapTable('updateByUniqueId', {
                                line_id: row.line_id,
                                row: row
                            });
                        }
                        console.log("Updated local table after entity text replacement.");
                    }, 100);
                }
            }, 'json');
    } else {
        $edit_lexicon_form[0].reportValidity();
    }
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