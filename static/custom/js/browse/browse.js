// Network Documentation: https://visjs.github.io/vis-network/docs/network/

// NOTE: The following are global constants:
// * 'API_URL'
// * 'VARIABLE_PREFIX' and 'VARIABLE_SUFFIX'
// * 'INITIAL_QUERY' and 'NODE_QUERY_TEMPLATE'
// They must be set before inclusion of this file
// They are set in query.html file


var NETWORK, ALL_NODES;
var HIGHLIGHT_ACTIVE = false;

var NODES_DATASET = new vis.DataSet();
var EDGES_DATASET = new vis.DataSet();

/* ------------------------------------- Elements ------------------------------------- */

const $browse_form = $("#browse-form");
const $seed_node = $("#input-seed-node");

const $physics_button = $("#toggle-physics");
const $toggle_icon = $("#toggle-icon");
const $download_button = $("#download-image");

/* ------------------------------------------------------------------------------------ */

/* ------------------------------------ Functions ------------------------------------ */

function toTitleCase(str) {
    return str.replace(/(?:^|\s)\w/g, function(match) {
        return match.toUpperCase();
    });
}

function prepare_network_data(nodes, relationships) {
    var dataset = {
        nodes: [],
        edges: []
    }

    var node_labels = [];
    var edge_labels = [];

    for (const [key, node] of Object.entries(nodes)) {
        var group_id = node_labels.indexOf(node.labels[0]) + 1;
        if (!group_id) {
            node_labels.push(node.labels[0]);
            group_id = node_labels.length;
        }
        var title = [
            `Labels: ${node.labels.join(", ")}`
        ];
        for (const [prop_name, prop_val] of Object.entries(node.properties)) {
            if (!prop_name.startsWith("__") && prop_val) {
                var prop_display_name = prop_name.indexOf("_") > -1 ? prop_name : toTitleCase(prop_name);
                var prop_display_val = prop_val.toString().indexOf(";") > -1 ? prop_val.split(";").join(", ") : prop_val;
                title.push(`${prop_display_name}: ${prop_display_val}`);
            }
        }

        dataset.nodes.push({
            id: node.id,
            label: node.properties.lemma,
            title: title.join("\n"),
            value: 3,
            pagerank: 1,
            group: group_id
        });
    }
    for (const [key, relationship] of Object.entries(relationships)) {
        var group_id = edge_labels.indexOf(relationship.label) + 1;
        if (!group_id) {
            edge_labels.push(relationship.label);
            group_id = edge_labels.length;
        }
        var title = [
            `Relation: ${relationship.label}`,
        ];
        for (const [prop_name, prop_val] of Object.entries(relationship.properties)) {
            if (!prop_name.startsWith("__") && prop_val) {
                var prop_display_name = prop_name.indexOf("_") > -1 ? prop_name : toTitleCase(prop_name);
                var prop_display_val = prop_val.toString().indexOf(";") > -1 ? prop_val.split(";").join(", ") : prop_val;
                title.push(`${prop_display_name}: ${prop_display_val}`);
            }
        }

        dataset.edges.push({
            id: relationship.id,
            from: relationship.start.id,
            to: relationship.end.id,
            label: relationship.label,
            title: title.join("\n"),
            arrows: {
                to: {
                    enabled: true
                }
            },
            value: 3,
        });
    }

    NODES_DATASET.clear()
    NODES_DATASET.update(dataset.nodes);

    EDGES_DATASET.clear()
    EDGES_DATASET.update(dataset.edges);
}

function setup_network() {
    var container = document.getElementById('graph');
    var options = {
        nodes: {
            shape: 'dot',
            scaling: {
                min: 12,
                max: 24,
                label: {
                    min: 15,
                    max: 30,
                    drawThreshold: 12,
                    maxVisible: 30
                }
            },
            font: {
                size: 16,
                face: 'Times New Roman'
            }
        },
        edges: {
            width: 0.15,
            color: {
                inherit: 'both'
            },
            scaling: {
                min: 1,
                max: 5,
                label: {
                    min: 10,
                    max: 25,
                    drawThreshold: 5,
                    maxVisible: 20
                }
            },
            font: {
                size: 5,
                face: 'mono'
            }
        },
        physics: {
            forceAtlas2Based: {
                gravitationalConstant: -30,
                centralGravity: 0.003,
                springLength: 200,
                springConstant: 0.15
            },
            maxVelocity: 150,
            solver: 'forceAtlas2Based',
            timestep: 0.35,
            stabilization: {
                iterations: 120
            }
        },
        interaction: {
            tooltipDelay: 100,
            hideEdgesOnDrag: false,
            hideEdgesOnZoom: false,
            hover: true
        },
    };
    var data = {
        nodes: NODES_DATASET,
        edges: EDGES_DATASET
    }

    NETWORK = new vis.Network(container, data, options);

    // get a JSON object
    ALL_NODES = NODES_DATASET.get({
        returnType: "Object"
    });
    NETWORK.on("afterDrawing", function (ctx) {
        var data_url = ctx.canvas.toDataURL();
        $download_button.data("src", data_url);
    });
    NETWORK.on("click", neighbourhood_highlight);
    NETWORK.on("oncontext", explore_node)
}

// Query


function run_cypher_query(cypher_query_text, response_handler) {
    $.post(API_URL, {
        action: "query",
        query: cypher_query_text,
    },
    function (response) {
        if (response.success) {
            $.notify({
                message: response.message
            }, {
                type: "success"
            });
            response_handler(response);
        } else {
            console.log(response.message);
            $.notify({
                message: response.message
            }, {
                type: "danger"
            });
        }
        if (response.warning) {
            console.log(response.warning);
            $.notify({
                message: response.warning
            }, {
                type: "warning"
            })
        }
    },
    'json');
}

function process_query_response(response) {
    // Create Node and Edge datasets suitable for Vis.js Network
    prepare_network_data(response.nodes, response.edges);

    // Draw the network graph
    setup_network();
}

/* -------------------------------------- Actions -------------------------------------- */


function explore_node(params) {
    params.event.preventDefault();
    const selected_node_id = NETWORK.getNodeAt(params.pointer.DOM);
    const selected_node = ALL_NODES[selected_node_id];
    const cypher_query_text = $('<textarea />').html(NODE_QUERY_TEMPLATE).text().replace("{}", selected_node.label);
    run_cypher_query(cypher_query_text, process_query_response);
}

function neighbourhood_highlight(params) {
    // if something is selected:
    var selected_nodes = [];
    var selected_edges = [];
    var highlight_first_degree = true;
    var highlight_second_degree = true;

    if (params.nodes.length > 0) {
        selected_nodes = params.nodes;
    } else if (params.edges.length > 0) {
        selected_edges = params.edges;
        highlight_second_degree = false;
    }

    if (selected_nodes.length > 0 || selected_edges.length > 0) {
        HIGHLIGHT_ACTIVE = true;
        var i, j;
        var degrees = 2;

        // mark all nodes as hard to read.
        for (var node_id in ALL_NODES) {
            ALL_NODES[node_id].color = 'rgba(225,225,225, 0.5)';
            if (ALL_NODES[node_id].hiddenLabel === undefined) {
                ALL_NODES[node_id].hiddenLabel = ALL_NODES[node_id].label;
                ALL_NODES[node_id].label = undefined;
            }
            ALL_NODES[node_id].value = ALL_NODES[node_id].pagerank / 2;
        }

        var connected_nodes = [];
        var first_degree_nodes = [];
        for (const selected_node of selected_nodes) {
            first_degree_nodes.push(...NETWORK.getConnectedNodes(selected_node));
        }
        for (const selected_edge of selected_edges) {
            first_degree_nodes.push(...NETWORK.getConnectedNodes(selected_edge));
        }

        for (first_degree_node of first_degree_nodes) {
            if (!selected_nodes.includes(first_degree_node)) {
                connected_nodes.push(first_degree_node);
            }
        }

        if (selected_nodes.length + connected_nodes.length >= 1) {
            NETWORK.fit({
                nodes: [...selected_nodes, ...connected_nodes],
                animation: false
            });
        }

        if (highlight_second_degree) {
            var all_connected_nodes = [];

            // get the second degree nodes
            for (i = 1; i < degrees; i++) {
                for (j = 0; j < connected_nodes.length; j++) {
                    var second_degree_nodes = NETWORK.getConnectedNodes(connected_nodes[j]);
                    for (var k = 0; k < second_degree_nodes.length; k++) {
                        var second_degree_node = second_degree_nodes[k];
                        if (!connected_nodes.includes(second_degree_node)) {
                            all_connected_nodes.push(second_degree_node);
                        }
                    }
                }
            }

            // all second degree nodes get a different color and their label back
            for (i = 0; i < all_connected_nodes.length; i++) {
                ALL_NODES[all_connected_nodes[i]].color = 'rgba(175,175,175,0.75)';
                if (ALL_NODES[all_connected_nodes[i]].hiddenLabel !== undefined) {
                    ALL_NODES[all_connected_nodes[i]].label = ALL_NODES[all_connected_nodes[i]].hiddenLabel;
                    ALL_NODES[all_connected_nodes[i]].hiddenLabel = undefined;
                }
                ALL_NODES[all_connected_nodes[i]].value = ALL_NODES[all_connected_nodes[i]].pagerank * 2;
            }
        }

        // all first degree nodes get their own color and their label back
        for (connected_node of connected_nodes) {
            if (selected_nodes.length > 1) {
                ALL_NODES[connected_node].color = 'rgba(115,115,115,0.75)';
            } else {
                ALL_NODES[connected_node].color = undefined;
            }
            if (ALL_NODES[connected_node].hiddenLabel !== undefined) {
                ALL_NODES[connected_node].label = ALL_NODES[connected_node].hiddenLabel;
                ALL_NODES[connected_node].hiddenLabel = undefined;
            }
            ALL_NODES[connected_node].value = ALL_NODES[connected_node].pagerank * 2;
        }

        // the main nodes get their own color and label back.
        for (selected_node of selected_nodes) {
            ALL_NODES[selected_node].color = undefined;
            if (ALL_NODES[selected_node].hiddenLabel !== undefined) {
                ALL_NODES[selected_node].label = ALL_NODES[selected_node].hiddenLabel;
                ALL_NODES[selected_node].hiddenLabel = undefined;
            }
            ALL_NODES[selected_node].value = ALL_NODES[selected_node].pagerank * 3;
        }
    } else if (HIGHLIGHT_ACTIVE === true) {
        // reset all nodes
        for (var node_id in ALL_NODES) {
            ALL_NODES[node_id].color = undefined;
            if (ALL_NODES[node_id].hiddenLabel !== undefined) {
                ALL_NODES[node_id].label = ALL_NODES[node_id].hiddenLabel;
                ALL_NODES[node_id].hiddenLabel = undefined;
            }
            ALL_NODES[node_id].value = ALL_NODES[node_id].pagerank;
        }
        HIGHLIGHT_ACTIVE = false
        NETWORK.fit({
            animation: false
        });
    }

    // transform the object into an array
    var update_array = [];
    for (node_id in ALL_NODES) {
        if (ALL_NODES.hasOwnProperty(node_id)) {
            update_array.push(ALL_NODES[node_id]);
        }
    }
    NODES_DATASET.update(update_array);
}

/* ----------------------------------------------------------------------------------- */


/* -------------------------------------- Events -------------------------------------- */

// Query
$browse_form.submit(function(e) {
    e.preventDefault();
    const seed_node_lemma = $seed_node.val();
    const cypher_query_text = $('<textarea />').html(NODE_QUERY_TEMPLATE).text().replace("{}", seed_node_lemma);
    run_cypher_query(cypher_query_text, process_query_response);
});

// Physics Enable/Disable
$physics_button.click(function () {
    var physics_on = $toggle_icon.hasClass("fa-lock");
    if (physics_on) {
        NETWORK.setOptions({physics: false});
        $toggle_icon.removeClass("fa-lock");
        $toggle_icon.addClass("fa-unlock");
    } else {
        NETWORK.setOptions({physics: true});
        $toggle_icon.removeClass("fa-unlock");
        $toggle_icon.addClass("fa-lock");
    }
});

// Snapshot
$download_button.click(function() {
    var download_anchor = document.createElement('a');
    download_anchor.href = $download_button.data('src');
    download_anchor.download = 'graph.png'
    document.body.appendChild(download_anchor);
    download_anchor.click();
    document.body.removeChild(download_anchor);
});

/* ------------------------------------------------------------------------------------ */

/* --------------------------------------- Main --------------------------------------- */

$(document).ready(function () {
    run_cypher_query(INITIAL_QUERY, process_query_response);
    $seed_node.autoComplete();
});

/* ------------------------------------------------------------------------------------ */
