/* ******************************* Elements ******************************** */

const $query_builder = $("#query-builder");

const $query_select = $("#query-select");
const $language_select = $("#language-select");
const $cypher_input = $("#cypher-text");
const $edit_button = $("#edit-cypher");
const $submit_button = $("#submit-query");
const $download_button = $("#download-image");

const $query_input = $("#query-input");
const $query_input_container = $("#query-input-container");
const $query_text = $("#query-text");

const $sample_entity = $("#sample-entity");
const $sample_entity_type = $("#sample-entity-type");
const $sample_relation = $("#sample-relation");
const $sample_relation_detail = $("#sample-relation-detail");

const $result_container = $("#result-container")
const $result_table = $("#result-viewer");

/* ******************************* Constants ******************************* */

const query_input_element_prefix = "query-input-";

/* ******************************* Functions ******************************* */

function update_query() {
    var language = $language_select.val();
    var cypher = $query_select.data('cypher');
    var query_text = $query_select.data(language);
    var input_elements = $query_select.data('input');

    for (const input_element of input_elements) {
        var $element = $("#" + query_input_element_prefix + input_element.id);
        var element_value = $element.val().trim();
        if (element_value) {
            cypher = cypher.replace(`${variable_prefix}${input_element.id}${variable_suffix}`, element_value);
            query_text = query_text.replace(`${variable_prefix}${input_element.id}${variable_suffix}`, `"${element_value}"`);
        }
    }
    $cypher_input.val(cypher);
    $query_text.html(query_text);
}

function update_custom_query() {
    if ($edit_button.prop('disabled')) {
        $query_text.html($cypher_input.val());
    }
}

// function prepare_download_data(nodes, relationships) {
//     var header = "data:text/plain;charset=utf-8,";
//     var lines = [];
//     for (const [key, node] of Object.entries(nodes)) {
//         lines.push(JSON.stringify(node));
//     }
//     for (const [key, relationship] of Object.entries(relationships)) {
//         lines.push(JSON.stringify(relationship));
//     }
//     data = header + encodeURIComponent((lines).join("\n"));
//     $download_button.attr('href', data);
// }

function update_result_table(response) {
    const results = [];
    const headers = [];
    var output_order = $result_table.data('output-order');
    if (response.matches.length > 0) {
        if (typeof output_order == 'undefined' || $edit_button.prop('disabled')) {
            output_order = Object.keys(response.matches[0]);
        }
        for (const key of output_order) {
            headers.push({
                title: key,
                field: key,
            });
        }
        for (const match of response.matches) {
            var row = {}
            row.ids = {};
            for (const key of output_order) {
                var element_ids = [];
                if (Array.isArray(match[key])) {
                    if ((match[key].length == 3) && Array.isArray(match[key][1])) {
                        element_ids = [match[key][0], ...match[key][1], match[key][2]];
                    } else {
                        element_ids = match[key];
                    }
                } else {
                    element_ids = [match[key]];
                }
                row.ids[key] = {
                    'nodes': [],
                    'edges': []
                }
                row[key] = [];

                for (element_id of element_ids) {
                    if (element_id in response.nodes) {
                        row.ids[key].nodes.push(element_id);
                        var node_object = response.nodes[element_id];
                        row[key].push(
                            `<span title="Line: ${node_object.properties.line_id}\nAnnotator: ${node_object.properties.annotator}">${node_object.properties.lemma} (${node_object.labels[0]})</span>`
                        );
                    }
                    else if (element_id in response.edges) {
                        row.ids[key].edges.push(element_id);
                        var edge_object = response.edges[element_id];
                        var edge_repr = `<span title="Line: ${edge_object.properties.line_id}\nAnnotator: ${edge_object.properties.annotator}">`;
                        edge_repr += edge_object.label;
                        if (edge_object.properties.detail && edge_object.properties.detail.length) {
                            edge_repr += ` (${edge_object.properties.detail})`;
                        }
                        edge_repr += '</span>';
                        row[key].push(edge_repr);
                    }
                    else {
                        row[key].push(`${element_id}`);
                    }
                }
                row[key] = row[key].join(" + ");
            }
            results.push(row);
        }
    }
    $result_table.bootstrapTable('destroy');
    $result_table.bootstrapTable({
        columns: headers,
        exportTypes: ['csv', 'json', 'txt', 'excel'],
        exportOptions: {
            fileName: function () {
               return 'result'
            }
         }

    });
    $result_table.bootstrapTable('load', results);
}

function process_query_response(response) {
    // Note: Network related functions are in "network.js"
    // Create Node and Edge datasets suitable for Vis.js Network
    prepare_network_data(response.nodes, response.edges);

    // Draw the network graph
    draw();

    // Show result in the table
    update_result_table(response);

    // Attach data to the download button
    // prepare_download_data(response.nodes, response.edges);
}

/* ******************************** Events ********************************* */
// 'variable_prefix' and 'variable_suffix' are global constants
// They must be set before inclusion of this file
// They are set in query.html file

$language_select.on("changed.bs.select", function (event, index, is_selected, old_value) {
    $query_select.find('option').each(function (index, element) {
        element.innerHTML = element.dataset[$language_select.val()];
    });
    $query_select.find('optgroup').each(function (index, element) {
        $(element).attr('label', element.dataset[$language_select.val()]);
    });
    $query_select.selectpicker('refresh');
});

$query_select.on("changed.bs.select", function (event, index, is_selected, old_value) {
    var selected_option = $query_select.find('option')[index];
    var input_elements = JSON.parse(decodeURIComponent(selected_option.dataset.inputElements));
    var output_order = JSON.parse(decodeURIComponent(selected_option.dataset.outputOrder));
    $result_table.data('output-order', output_order);

    $query_input_container.empty();

    if (input_elements.length > 0) {
        $query_input.removeClass('d-none');
    } else {
        $query_input.addClass('d-none');
    }

    $query_select.data({
        english: selected_option.dataset.english,
        sanskrit: selected_option.dataset.sanskrit,
        cypher: selected_option.dataset.cypher,
        input: input_elements
    });

    for (const [idx, input_element] of input_elements.entries()) {
        if (input_element.type === "entity") {
            var $input_element = $sample_entity.clone();
            var attribute_to_update = 'placeholder';
        }
        if (input_element.type === "entity_type") {
            var $input_element = $sample_entity_type.clone();
            var attribute_to_update = 'title';
        }
        if (input_element.type === "relation") {
            var $input_element = $sample_relation.clone();
            var attribute_to_update = 'title';
        }
        if (input_element.type === "relation_detail") {
            var $input_element = $sample_relation_detail.clone();
            var attribute_to_update = 'placeholder';
        }

        var current_value = $input_element.attr(attribute_to_update);
        var updated_value = current_value.replace(
            "{}",
            `${variable_prefix}${input_element.id}${variable_suffix}`
        );
        $input_element.attr(attribute_to_update, updated_value);

        $input_element.attr("id", query_input_element_prefix + input_element.id);

        if (input_elements.length == 1) {
            var padding_class = ''
        } else {
            var padding_class = (idx == 0) ? 'pr-0' : (idx == input_elements.length - 1) ? 'pl-1' : 'pr-0 pl-1';
        }

        var $column = $('<div />').addClass(`col-sm ${padding_class}`).appendTo($query_input_container);
        $input_element.appendTo($column);
        if ($input_element.is('select')) {
            $input_element.selectpicker();
            $input_element.on('change', function () {
                update_query();
            });
        }
        if ($input_element.is('input:text')) {
            if (input_element.type === "entity"){
                $input_element.autoComplete();
                // TODO: Auto-complete for relation_detail?
            }
            $input_element.on('keyup', function () {
                update_query();
            });
            $input_element.on('autocomplete.select', function (evt, item) {
                update_query();
            });
        }
    }
    update_query();

    $query_text.removeClass('d-none');
    $cypher_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    $edit_button.prop('disabled', false);
});

$result_table.on('click-cell.bs.table', function (event, field, value, row, $element) {
    var target = row.ids[field];
    // not the same as params when an actual click is performed
    // only nodes and edges properties are required for neighbourhood_highlight
    var params = {
        nodes: target.nodes,
        edges: target.edges
    }
    neighbourhood_highlight(params);
});

$cypher_input.on('keyup', update_custom_query);
$cypher_input.on('change', update_custom_query);

$edit_button.click(function () {
    $cypher_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
    $edit_button.prop('disabled', true);
});

$download_button.click(function() {
    var download_anchor = document.createElement('a');
    download_anchor.href = $download_button.data('src');
    download_anchor.download = 'graph.png'
    document.body.appendChild(download_anchor);
    download_anchor.click();
    document.body.removeChild(download_anchor);
});