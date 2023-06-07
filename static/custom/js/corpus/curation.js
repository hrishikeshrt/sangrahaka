
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