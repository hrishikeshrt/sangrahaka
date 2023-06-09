
$edit_lexicon_submit_button.on('click', function (e) {
    const line_id = $line_id_entity.val();
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
                    // refresh_row_data(line_id, setup_entity_annotation); ???
                    // If we call "refresh_row_data" at the start of every setup_entity_annotation
                    // we wouldn't need to do anything here. However, that may be unnecessarily costly
                    // Other option can be to figure out which "lines" need to be refreshed and just
                    // refresh those

                    // NOTE: potential bug when there's an unconfirmed relation using an existing entity and we change the lexicon
                    // TODO: investigate and fix if required
                    const current_text = $edit_lexicon_current_lemma.val().trim();
                    const replacement_text = $edit_lexicon_replacement_lemma.val().trim();

                    // update local entity list
                    $.each($entity_list.find("div.entity-lemma"), function () {
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


$edit_node_label_submit_button.on('click', function (e) {
    const line_id = $line_id_entity.val();
    $edit_node_label_modal.modal('hide');
    if ($edit_node_label_form[0].checkValidity()) {
        $.post(API_URL, {
                action: "update_node_label_id",
                node_id: $edit_node_label_node_id.val(),
                old_label_id: $edit_node_label_current_label.selectpicker('val'),
                new_label_id: $edit_node_label_replacement_label.selectpicker('val'),
            },
            function (response) {
                $.notify({
                    message: response.message
                }, {
                    type: response.style
                });
                if (response.success) {
                    $.notify({
                        message: "Please refresh row data for updating the list."
                    }, {
                        type: "warning"
                    });
                    // TODO: Success Handler
                    // refresh_row_data(line_id, setup_entity_annotation); ???
                    // If we call "refresh_row_data" at the start of every setup_entity_annotation
                    // we wouldn't need to do anything here. However, that may be unnecessarily costly
                    // Other option can be to figure out which "lines" need to be refreshed and just
                    // refresh those
                }
            }, 'json');
    } else {
        $edit_node_label_form[0].reportValidity();
    }
});


$edit_relation_label_submit_button.on('click', function (e) {
    const line_id = $line_id_entity.val();
    $edit_relation_label_modal.modal('hide');
    if ($edit_relation_label_form[0].checkValidity()) {
        $.post(API_URL, {
                action: "update_relation_label_id",
                relation_id: $edit_relation_label_relation_id.val(),
                old_label_id: $edit_relation_label_current_label.selectpicker('val'),
                new_label_id: $edit_relation_label_replacement_label.selectpicker('val'),
            },
            function (response) {
                $.notify({
                    message: response.message
                }, {
                    type: response.style
                });
                if (response.success) {
                    $.notify({
                        message: "Please refresh row data for updating the list."
                    }, {
                        type: "warning"
                    });
                    // TODO: Success Handler
                    // refresh_row_data(line_id, setup_entity_annotation); ???
                    // If we call "refresh_row_data" at the start of every setup_entity_annotation
                    // we wouldn't need to do anything here. However, that may be unnecessarily costly
                    // Other option can be to figure out which "lines" need to be refreshed and just
                    // refresh those
                }
            }, 'json');
    } else {
        $edit_relation_label_form[0].reportValidity();
    }
});