// Storage
const storage = window.localStorage;

// Storage Keys
const KEY_DATA_COLLAPSIBLE_SHOW = "data_collapsible_show";
const KEY_ONTOLOGY_TAB_ACTIVE = "ontology_tab_active";

// Parent Elements
const DATA_COLLAPSIBLE_PARENT_ID = "manage_data";
const DATA_COLLAPSIBLE_DEFAULT_SHOW_ID = "corpus_container";
const ONTOLOGY_TAB_PARENT_ID = "labels-tab";

/* ********************************* Main ********************************* */

$(document).ready(function () {
    // Render CustomFile input element
    bsCustomFileInput.init();

    // Display active elements
    const data_collapsible_show_id  = storage.getItem(KEY_DATA_COLLAPSIBLE_SHOW);
    if (!data_collapsible_show_id) {
        data_collapsible_show_id = DATA_COLLAPSIBLE_DEFAULT_SHOW_ID;
    };
    $(`#${data_collapsible_show_id}`).collapse('show');

    const ontology_tab_active_id = storage.getItem(KEY_ONTOLOGY_TAB_ACTIVE);
    if (ontology_tab_active_id) {
        $(`#${ontology_tab_active_id}`).tab('show');
    };
});

/* ******************************** Events ******************************** */

$(`#${DATA_COLLAPSIBLE_PARENT_ID} .collapse`).on('shown.bs.collapse', function (event) {
    const target_element = event.target;
    const target_id = target_element.id;
    storage.setItem(KEY_DATA_COLLAPSIBLE_SHOW, target_id);
});

$(`#${ONTOLOGY_TAB_PARENT_ID} .ontology-tab`).on('shown.bs.tab', function (event) {
    const target_element = event.target;
    const target_id = target_element.id;
    storage.setItem(KEY_ONTOLOGY_TAB_ACTIVE, target_id);
});
