// Annotation Event Handlers
// Note: Constants in CAPITAL letters are declared in corpus.html

/* ******************** Entity Annotation - BEGIN ******************** */

$add_entity_button.on('click', function(e) {
    if ($form_prepare_entity[0].checkValidity() && $line_id_entity.val() != "") {

        var _root = unnamed_formatter($line_id_entity.val(), $entity_root.val().trim(), UNNAMED_PREFIX);
        var _type = $entity_type.val().trim();

        var entity_html = entity_formatter(_root, _type, "list-group-item-warning", CURRENT_USERNAME);
        $entity_list.append(entity_html);
        $('[name="entity"]').bootstrapToggle();

        // update local unconfirmed storage
        var unconfirmed = storage.getItem($line_id_entity.val());
        if (unconfirmed === null) {
            unconfirmed = '[]';
        }
        unconfirmed = JSON.parse(unconfirmed);
        unconfirmed.push({
            'root': _root,
            'type': _type,
            'annotator': CURRENT_USERNAME,
            'is_deleted': false
        });
        storage.setItem($line_id_entity.val(), JSON.stringify(unconfirmed));
    } else {
        $form_prepare_entity[0].reportValidity();
    }
});

$confirm_entity_button.on('click', function(e) {
    var entity_add = [];
    var entity_delete = [];
    $.each($entity_list.find('[name="entity"]'), function () {
        if ($(this).closest("li").hasClass("list-group-item-warning") && $(this).is(":checked")) {
            entity_add.push($(this).val());
        }
        if (!$(this).closest("li").hasClass("list-group-item-warning") && !$(this).is(":checked")) {
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
                    $(this).closest('li').removeClass("list-group-item-warning");
                    var entity_values = $(this).val().split('$');
                    entity_objects.push({
                        'root': entity_values[0],
                        'type': entity_values[1],
                        'annotator': CURRENT_USERNAME,
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
    if ($form_prepare_relation[0].checkValidity() && $line_id_relation.val() != "") {
        const form_prepare_relation = Object.values($form_prepare_relation[0]).reduce(function (obj,field) {
            obj[field.name] = field.value;
            return obj
        }, {});

        const relation_source_value = form_prepare_relation["input_relation_source"];
        const relation_source_text = form_prepare_relation["input_relation_source_text"];
        const relation_target_value = form_prepare_relation["input_relation_target"];
        const relation_target_text = form_prepare_relation["input_relation_target_text"];

        var _source = unnamed_formatter($line_id_relation.val(), relation_source_text.trim(), UNNAMED_PREFIX);
        var _detail = $relation_detail.val().trim();
        var _label = $relation_label.val().trim();
        var _target = unnamed_formatter($line_id_relation.val(), relation_target_text.trim(), UNNAMED_PREFIX);

        var relation_html = relation_formatter(_source, _label, _target, _detail, "list-group-item-warning", CURRENT_USERNAME);
        $relation_list.append(relation_html);
        $('[name="relation"]').bootstrapToggle();

        // update local unconfirmed storage
        var unconfirmed_relations = storage.getItem($line_id_relation.val() + '_relations');
        if (unconfirmed_relations === null) {
            unconfirmed_relations = '[]';
        }
        unconfirmed_relations = JSON.parse(unconfirmed_relations);
        unconfirmed_relations.push({
            'source': _source,
            'label': _label,
            'detail': _detail,
            'target': _target,
            'annotator': CURRENT_USERNAME,
            'is_deleted': false
        });
        storage.setItem($line_id_relation.val() + '_relations', JSON.stringify(unconfirmed_relations));
    } else {
        $form_prepare_relation[0].reportValidity();
    }
});

$confirm_relation_button.on('click', function(e) {
    var relation_add = [];
    var relation_delete = [];
    $.each($relation_list.find('[name="relation"]'), function () {
        if ($(this).closest("li").hasClass("list-group-item-warning") && $(this).is(":checked")) {
            relation_add.push($(this).val());
        }
        if (!$(this).closest("li").hasClass("list-group-item-warning") && !$(this).is(":checked")) {
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
                    $(this).closest('li').removeClass("list-group-item-warning");
                    var relation_values = $(this).val().split('$');
                    relation_objects.push({
                        'source': relation_values[0],
                        'label': relation_values[1],
                        'target': relation_values[2],
                        'detail': relation_values[3],
                        'annotator': CURRENT_USERNAME,
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

        var action_html = action_formatter(_label, _actor_label, _actor, "list-group-item-warning", CURRENT_USERNAME);
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
        if ($(this).closest("li").hasClass("list-group-item-warning") && $(this).is(":checked")) {
            action_add.push($(this).val());
        }
        if (!$(this).closest("li").hasClass("list-group-item-warning") && !$(this).is(":checked")) {
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
                    $(this).closest('li').removeClass("list-group-item-warning");
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