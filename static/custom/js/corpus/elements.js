const $corpus_table = $("#corpus_viewer");

const $refresh_row_data_buttons = $(".refresh-row-data");

// Entity Annotation
const $form_prepare_entity = $("#form_prepare_entity");
const $line_id_entity = $("#line_id_entity");
const $entity_root = $("#input_entity_root");
const $entity_type = $("#input_entity_type");

const $add_entity_button = $("#add_entity");

const $confirm_entity_button = $("#confirm_entity_list");
const $entity_list = $("#entity_list");

// Entity Edit

// Edit Entity Text
const $edit_lexicon_modal = $("#edit-lexicon-modal");
const $edit_lexicon_form = $("#edit-lexicon-form");
const $edit_lexicon_submit_button = $("#edit-lexicon-submit");
const $edit_lexicon_node_id = $("#edit-lexicon-node-id");
const $edit_lexicon_lexicon_id = $("#edit-lexicon-lexicon-id");
const $edit_lexicon_current_lemma = $("#edit-lexicon-current-lemma");
const $edit_lexicon_replacement_lemma = $("#edit-lexicon-replacement-lemma");

// Edit Entity Type
const $edit_node_label_modal = $("#edit-node-label-modal");
const $edit_node_label_form = $("#edit-node-label-form");
const $edit_node_label_submit_button = $("#edit-node-label-submit");
const $edit_node_label_node_id = $('#edit-node-label-node-id');
const $edit_node_label_lexicon = $('#edit-node-label-lexicon');
const $edit_node_label_node_label = $('#edit-node-label-node-label');
const $edit_node_label_current_label = $("#edit-node-label-current-label");
const $edit_node_label_replacement_label = $("#edit-node-label-replacement-label");

// Relation Annotation
const $form_prepare_relation = $("#form_prepare_relation");
const $line_id_relation = $("#line_id_relation");
const $relation_source = $("#input_relation_source");
const $relation_label = $("#input_relation_label");
const $relation_detail = $("#input_relation_detail");
const $relation_target = $("#input_relation_target");

const $add_relation_button = $("#add_relation")

const $confirm_relation_button = $("#confirm_relation_list");
const $relation_list = $("#relation_list");

// Edit Relation Type
const $edit_relation_label_modal = $("#edit-relation-label-modal");
const $edit_relation_label_form = $("#edit-relation-label-form");
const $edit_relation_label_submit_button = $("#edit-relation-label-submit");
const $edit_relation_label_relation_id = $('#edit-relation-label-relation-id');
const $edit_relation_label_src_lexicon = $('#edit-relation-label-source-lexicon');
const $edit_relation_label_src_label = $('#edit-relation-label-source-label');
const $edit_relation_label_relation_label = $('#edit-relation-label-relation-label');
const $edit_relation_label_relation_detail = $('#edit-relation-label-relation-detail');
const $edit_relation_label_dst_lexicon = $('#edit-relation-label-target-lexicon');
const $edit_relation_label_dst_label = $('#edit-relation-label-target-label');

const $edit_relation_label_current_label = $("#edit-relation-label-current-label");
const $edit_relation_label_replacement_label = $("#edit-relation-label-replacement-label");

/*
// Action Annotation
const $form_prepare_action = $("#form_prepare_action");
const $line_id_action = $("#line_id_action");
const $action_label = $("#input_action_label");
const $action_actor_label = $("#input_action_actor_label");
const $action_actor = $("#input_action_actor");

const $add_action_button = $("#add_action")

const $confirm_action_button = $("#confirm_action_list");
const $action_list = $("#action_list");
*/


// Globals
var storage = window.localStorage;

const KEY_CURRENT_INDEX = "current_index";
const KEY_NEXT_INDEX = "next_index";
const KEY_CURRENT_UNIQUE_ID = "current_unique_id";
const KEY_NEXT_UNIQUE_ID = "next_unique_id";
