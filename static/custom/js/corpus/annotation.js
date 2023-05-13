// Annotation Event Handlers
// Note: Constants in CAPITAL letters are declared in corpus.html

/* ******************** Entity Annotation - BEGIN ******************** */

$add_entity_button.on('click', function(e) {
    if ($form_prepare_entity[0].checkValidity() && $line_id_entity.val() != "") {

        var _lemma = unnamed_formatter($line_id_entity.val(), $entity_root.val().trim(), UNNAMED_PREFIX);
        var _label = $entity_type.val().trim();

        const entity_object = {
            "lemma": {
                "lemma": _lemma,
            },
            "label": {
                "label": _label
            },
            "annotator": {
                "id": CURRENT_USER_ID,
                "username": CURRENT_USERNAME,
            },
            "is_deleted": false
        };
        const entity_html = entity_formatter(entity_object, true);
        $entity_list.append(entity_html);
        $('[name="entity"]').bootstrapToggle();

        // update local unconfirmed storage
        var unconfirmed = storage.getItem($line_id_entity.val());
        if (unconfirmed === null) {
            unconfirmed = '[]';
        }
        unconfirmed = JSON.parse(unconfirmed);
        unconfirmed.push(entity_object);
        storage.setItem($line_id_entity.val(), JSON.stringify(unconfirmed));
    } else {
        $form_prepare_entity[0].reportValidity();
    }
});

$confirm_entity_button.on('click', function(e) {
    var entity_add = [];
    var entity_delete = [];
    $.each($entity_list.find('[name="entity"]'), function () {
        if ($(this).closest("li").hasClass("unconfirmed-entity") && $(this).is(":checked")) {
            entity_add.push($(this).val());
        }
        if (!$(this).closest("li").hasClass("unconfirmed-entity") && !$(this).is(":checked")) {
            entity_delete.push($(this).val());
        }
    });
    $.post(API_URL, {
        action: "update_entity",
        chapter_id: CHAPTER_ID,
        line_id: $line_id_entity.val(),
        entity_add: entity_add.join("##"),
        entity_delete: entity_delete.join("##")
    },
    function (response) {
        if (response.success) {
            $.notify({
                message: "Successfully updated!"
            }, {
                type: "success"
            });
            var entity_objects = [];
            // clear out the unconfirmed storage
            storage.removeItem($line_id_entity.val());

            // update local entity list
            $.each($entity_list.find('[name="entity"]'), function () {
                if ($(this).is(":checked")) {
                    $(this).closest('li').removeClass(["unconfirmed-entity", "list-group-item-warning"]);
                    var entity_values = $(this).val().split('$');
                    entity_objects.push({
                        'lemma': {
                            'lemma': entity_values[0]
                        },
                        'label': {
                            'label': entity_values[1]
                        },
                        'annotator': {
                            'id': CURRENT_USER_ID,
                            'username': CURRENT_USERNAME
                        },
                        'is_deleted': false
                    });
                    // all_roots.add("<option>" + entity_values[0] + "</option>");
                } else {
                    $(this).closest('li').detach();
                }
            });
            // update local table
            var current_row = $corpus_table.bootstrapTable('getRowByUniqueId', $line_id_entity.val());
            current_row.marked = true;
            current_row.entity = entity_objects;

            $corpus_table.bootstrapTable('updateByUniqueId', {
                line_id: current_row.line_id,
                row: current_row
            });
        } else {
            $.notify({
                message: "Something went wrong!"
            }, {
                type: "danger"
            });
        }
    },
    'json');
});

/* ******************** Entity Annotation - END ******************** */

/* ******************** Relation Annotation - BEGIN ******************** */

$add_relation_button.on('click', function(e) {
    const separator = "::";

    if ($form_prepare_relation[0].checkValidity() && $line_id_relation.val() != "") {
        const form_prepare_relation = Object.values($form_prepare_relation[0]).reduce(function (obj,field) {
            obj[field.name] = field.value;
            return obj
        }, {});

        // TODO:
        // * Can we avoid dependence on `name` parameters?
        // * Do we need to?
        const line_id = $line_id_relation.val();
        const relation_source_value = form_prepare_relation["input_relation_source"];
        const relation_source_text = form_prepare_relation["input_relation_source_text"];
        const relation_target_value = form_prepare_relation["input_relation_target"];
        const relation_target_text = form_prepare_relation["input_relation_target_text"];
        const relation_detail_value = form_prepare_relation["input_relation_detail"];
        const relation_detail_text = form_prepare_relation["input_relation_detail_text"];

        const _source_parts = relation_source_text.split(separator);
        const _target_parts = relation_target_text.split(separator);

        const _source_lemma = unnamed_formatter(line_id, _source_parts[0].trim(), UNNAMED_PREFIX);
        const _source_label = _source_parts[1].trim();
        const _source_node_id = relation_source_value;

        // NOTE: Currently, direct text is being used for detail, although it (mostly) signifies a node
        // This is primarily because we do not know yet if we'll require a non-node target ever, and if we don't
        // with text::category, we can get unique node-id, but in case we do, this saves us full-db change again.
        // When using <select>, _text is used to get direct text value,
        // else we can use _value
        const _detail = relation_detail_value;


        const _label = $relation_label.val().trim();

        const _target_lemma = unnamed_formatter(line_id, _target_parts[0].trim(), UNNAMED_PREFIX);
        const _target_label = _target_parts[1].trim();
        const _target_node_id = relation_target_value;

        const relation_object = {
            "source": {
                "id": _source_node_id,
                "lemma": _source_lemma,
                "label": _source_label
            },
            "label": {
                "label": _label
            },
            "detail": _detail,
            "target": {
                "id": _target_node_id,
                "lemma": _target_lemma,
                "label": _target_label
            },
            "annotator": {
                "id": CURRENT_USER_ID,
                "username": CURRENT_USERNAME,
            },
            "is_deleted": false
        };
        const relation_html = relation_formatter(relation_object, true);
        $relation_list.append(relation_html);
        $('[name="relation"]').bootstrapToggle();

        // update local unconfirmed storage
        var unconfirmed_relations = storage.getItem(line_id + '_relations');
        if (unconfirmed_relations === null) {
            unconfirmed_relations = '[]';
        }
        unconfirmed_relations = JSON.parse(unconfirmed_relations);
        unconfirmed_relations.push(relation_object);
        storage.setItem(line_id + '_relations', JSON.stringify(unconfirmed_relations));
    } else {
        $form_prepare_relation[0].reportValidity();
    }
});

$confirm_relation_button.on('click', function(e) {
    var relation_add = [];
    var relation_delete = [];
    $.each($relation_list.find('[name="relation"]'), function () {
        if ($(this).closest("li").hasClass("unconfirmed-relation") && $(this).is(":checked")) {
            relation_add.push($(this).val());
        }
        if (!$(this).closest("li").hasClass("unconfirmed-relation") && !$(this).is(":checked")) {
            relation_delete.push($(this).val());
        }
    });
    $.post(API_URL, {
        action: "update_relation",
        chapter_id: CHAPTER_ID,
        line_id: $line_id_relation.val(),
        relation_add: relation_add.join("##"),
        relation_delete: relation_delete.join("##")
    },
    function (response) {
        if (response.success) {
            $.notify({
                message: "Successfully updated!"
            }, {
                type: "success"
            });
            var relation_objects = [];
            // clear out the unconfirmed storage
            storage.removeItem($line_id_relation.val() + '_relations');

            // update local relation list
            $.each($relation_list.find('[name="relation"]'), function () {
                if ($(this).is(":checked")) {
                    $(this).closest('li').removeClass(["unconfirmed-relation", "list-group-item-warning"]);
                    var relation_values = $(this).val().split('$');
                    relation_objects.push({
                        'source': {
                            'id': relation_values[0],
                            'lemma': relation_values[4],
                            'label': relation_values[5]
                        },
                        'label': {
                            'id': relation_values[1],
                            'label': relation_values[6]
                        },
                        'target': {
                            'id': relation_values[2],
                            'lemma': relation_values[7],
                            'label': relation_values[8]
                        },
                        'detail': relation_values[3],
                        'annotator': {
                            'id': CURRENT_USER_ID,
                            'username': CURRENT_USERNAME
                        },
                        'is_deleted': false
                    });
                    // all_roots.add("<option>" + relation_values[0] + "</option>");
                    // all_roots.add("<option>" + relation_values[2] + "</option>");
                } else {
                    $(this).closest('li').detach();
                }
            });
            // update local table
            var current_row = $corpus_table.bootstrapTable('getRowByUniqueId', $line_id_relation.val());
            current_row.marked = true;
            current_row.relation = relation_objects;

            $corpus_table.bootstrapTable('updateByUniqueId', {
                line_id: current_row.line_id,
                row: current_row
            });
        } else {
            $.notify({
                message: "Something went wrong!"
            }, {
                type: "danger"
            });
        }
    },
    'json');
});

/* ******************** Relation Annotation - END ******************** */

/* ******************** Action Annotation - BEGIN ******************** */

$add_action_button.on('click', function(e) {
    if ($form_prepare_action[0].checkValidity() && $line_id_action.val() != "") {

        var _label = $action_label.val().trim();
        var _actor_label = $action_actor_label.val().trim();
        var _actor = unnamed_formatter($line_id_action.val(), $action_actor.val().trim(), UNNAMED_PREFIX);

        var action_html = action_formatter(_label, _actor_label, _actor, true, CURRENT_USERNAME);
        $action_list.append(action_html);
        $('[name="action"]').bootstrapToggle();

        // update local unconfirmed storage
        var unconfirmed_actions = storage.getItem($line_id_action.val() + '_actions');
        if (unconfirmed_actions === null) {
            unconfirmed_actions = '[]';
        }
        unconfirmed_actions = JSON.parse(unconfirmed_actions);
        unconfirmed_actions.push({
            'label': _label,
            'actor_label': _actor_label,
            'actor': _actor,
            'annotator': CURRENT_USERNAME,
            'is_deleted': false
        });
        storage.setItem($line_id_action.val() + '_actions', JSON.stringify(unconfirmed_actions));
    } else {
        $form_prepare_action[0].reportValidity();
    }
});

$confirm_action_button.on('click', function(e) {
    var action_add = [];
    var action_delete = [];
    $.each($action_list.find('[name="action"]'), function () {
        if ($(this).closest("li").hasClass("unconfirmed-action") && $(this).is(":checked")) {
            action_add.push($(this).val());
        }
        if (!$(this).closest("li").hasClass("unconfirmed-action") && !$(this).is(":checked")) {
            action_delete.push($(this).val());
        }
    });
    $.post(API_URL, {
        action: "update_action",
        chapter_id: CHAPTER_ID,
        line_id: $line_id_action.val(),
        action_add: action_add.join("##"),
        action_delete: action_delete.join("##")
    },
    function (response) {
        if (response.success) {
            $.notify({
                message: "Successfully updated!"
            }, {
                type: "success"
            });
            var action_objects = [];
            // clear out the unconfirmed storage
            storage.removeItem($line_id_action.val() + '_actions');

            // update local action list
            $.each($action_list.find('[name="action"]'), function () {
                if ($(this).is(":checked")) {
                    $(this).closest('li').removeClass(["unconfirmed-action", "list-group-item-warning"]);
                    var action_values = $(this).val().split('$');
                    action_objects.push({
                        'label': action_values[0],
                        'actor_label': action_values[1],
                        'actor': action_values[2],
                        'annotator': CURRENT_USERNAME,
                        'is_deleted': false
                    });
                    // all_roots.add("<option>" + action_values[0] + "</option>");
                    // all_roots.add("<option>" + action_values[2] + "</option>");
                } else {
                    $(this).closest('li').detach();
                }
            });
            // update local table
            var current_row = $corpus_table.bootstrapTable('getRowByUniqueId', $line_id_action.val());
            current_row.marked = true;
            current_row.action = action_objects;

            $corpus_table.bootstrapTable('updateByUniqueId', {
                line_id: current_row.line_id,
                row: current_row
            });
        } else {
            $.notify({
                message: "Something went wrong!"
            }, {
                type: "danger"
            });
        }
    },
    'json');
});

/* ******************** Action Annotation - END ******************** */