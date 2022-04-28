// https://visjs.github.io/vis-network/docs/network/

var network, all_nodes;
var highlight_active = false;

var nodes_dataset = new vis.DataSet();
var edges_dataset = new vis.DataSet();

const $physics_button = $("#toggle-physics");
const $toggle_icon = $("#toggle-icon");


$physics_button.click(function () {
    var physics_on = $toggle_icon.hasClass("fa-lock");
    if (physics_on) {
        network.setOptions({physics: false});
        $toggle_icon.removeClass("fa-lock");
        $toggle_icon.addClass("fa-unlock");
    } else {
        network.setOptions({physics: true});
        $toggle_icon.removeClass("fa-unlock");
        $toggle_icon.addClass("fa-lock");
    }
});

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
                var prop_display_val = prop_val.indexOf(";") > -1 ? prop_val.split(";").join(", ") : prop_val;
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
                var prop_display_val = prop_val.indexOf(";") > -1 ? prop_val.split(";").join(", ") : prop_val;
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

    nodes_dataset.clear()
    nodes_dataset.update(dataset.nodes);

    edges_dataset.clear()
    edges_dataset.update(dataset.edges);
}

function toTitleCase(str) {
    return str.replace(/(?:^|\s)\w/g, function(match) {
        return match.toUpperCase();
    });
}

function draw() {
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
            hideEdgesOnZoom: false
        },
    };
    var data = {
        nodes: nodes_dataset,
        edges: edges_dataset
    }

    network = new vis.Network(container, data, options);

    // get a JSON object
    all_nodes = nodes_dataset.get({
        returnType: "Object"
    });
    network.on("afterDrawing", function (ctx) {
        var data_url = ctx.canvas.toDataURL();
        $('#download-image').data("src", data_url);
    });
    network.on("click", neighbourhood_highlight);
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
        highlight_active = true;
        var i, j;
        var degrees = 2;

        // mark all nodes as hard to read.
        for (var node_id in all_nodes) {
            all_nodes[node_id].color = 'rgba(225,225,225, 0.5)';
            if (all_nodes[node_id].hiddenLabel === undefined) {
                all_nodes[node_id].hiddenLabel = all_nodes[node_id].label;
                all_nodes[node_id].label = undefined;
            }
            all_nodes[node_id].value = all_nodes[node_id].pagerank / 2;
        }

        var connected_nodes = [];
        var first_degree_nodes = [];
        for (const selected_node of selected_nodes) {
            first_degree_nodes.push(...network.getConnectedNodes(selected_node));
        }
        for (const selected_edge of selected_edges) {
            first_degree_nodes.push(...network.getConnectedNodes(selected_edge));
        }

        for (first_degree_node of first_degree_nodes) {
            if (!selected_nodes.includes(first_degree_node)) {
                connected_nodes.push(first_degree_node);
            }
        }

        if (selected_nodes.length + connected_nodes.length >= 1) {
            network.fit({
                nodes: [...selected_nodes, ...connected_nodes],
                animation: true
            });
        }

        if (highlight_second_degree) {
            var all_connected_nodes = [];

            // get the second degree nodes
            for (i = 1; i < degrees; i++) {
                for (j = 0; j < connected_nodes.length; j++) {
                    var second_degree_nodes = network.getConnectedNodes(connected_nodes[j]);
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
                all_nodes[all_connected_nodes[i]].color = 'rgba(175,175,175,0.75)';
                if (all_nodes[all_connected_nodes[i]].hiddenLabel !== undefined) {
                    all_nodes[all_connected_nodes[i]].label = all_nodes[all_connected_nodes[i]].hiddenLabel;
                    all_nodes[all_connected_nodes[i]].hiddenLabel = undefined;
                }
                all_nodes[all_connected_nodes[i]].value = all_nodes[all_connected_nodes[i]].pagerank * 2;
            }
        }

        // all first degree nodes get their own color and their label back
        for (connected_node of connected_nodes) {
            if (selected_nodes.length > 1) {
                all_nodes[connected_node].color = 'rgba(115,115,115,0.75)';
            } else {
                all_nodes[connected_node].color = undefined;
            }
            if (all_nodes[connected_node].hiddenLabel !== undefined) {
                all_nodes[connected_node].label = all_nodes[connected_node].hiddenLabel;
                all_nodes[connected_node].hiddenLabel = undefined;
            }
            all_nodes[connected_node].value = all_nodes[connected_node].pagerank * 2;
        }

        // the main nodes get their own color and label back.
        for (selected_node of selected_nodes) {
            all_nodes[selected_node].color = undefined;
            if (all_nodes[selected_node].hiddenLabel !== undefined) {
                all_nodes[selected_node].label = all_nodes[selected_node].hiddenLabel;
                all_nodes[selected_node].hiddenLabel = undefined;
            }
            all_nodes[selected_node].value = all_nodes[selected_node].pagerank * 3;
        }
    } else if (highlight_active === true) {
        // reset all nodes
        for (var node_id in all_nodes) {
            all_nodes[node_id].color = undefined;
            if (all_nodes[node_id].hiddenLabel !== undefined) {
                all_nodes[node_id].label = all_nodes[node_id].hiddenLabel;
                all_nodes[node_id].hiddenLabel = undefined;
            }
            all_nodes[node_id].value = all_nodes[node_id].pagerank;
        }
        highlight_active = false
        network.fit({
            animation: true
        });
    }

    // transform the object into an array
    var update_array = [];
    for (node_id in all_nodes) {
        if (all_nodes.hasOwnProperty(node_id)) {
            update_array.push(all_nodes[node_id]);
        }
    }
    nodes_dataset.update(update_array);
}