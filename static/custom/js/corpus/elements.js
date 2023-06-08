const $corpus_table = $("#corpus_viewer");

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
