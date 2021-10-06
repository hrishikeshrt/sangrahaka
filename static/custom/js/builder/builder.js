/* ------------------------------- Elements ------------------------------- */

const $network_container = $("#graph-builder");
const $node_operation = $("#node-operation");
const $edge_operation = $("#edge-operation");

const $node_label = $("#node-label");
const $node_type = $("#node-type");
const $node_query = $("#node-query");
const $node_save_button = $("#node-save-button");
const $node_cancel_button = $("#node-cancel-button");
const $node_popup = $("#node-popup");

const $edge_label = $("#edge-label")
const $edge_query = $("#edge-query");
const $edge_save_button = $("#edge-save-button");
const $edge_cancel_button = $("#edge-cancel-button");
const $edge_popup = $("#edge-popup");

// Note: Underlying DOM objects of jQuery objects can be accessed by $obj[0]

/* ------------------------------- Network ------------------------------- */

// Network Objects
var builder_network = null;

// Initial Network
var builder_network_data = {
  nodes: [],
  edges: []
}

function builder_draw() {
  builder_destroy();

  // create a Network
  var container = $network_container[0];
  var options = {
    interaction: {
      multiselect: true
    },
    edges: {
      arrows: {
        to: {
          enabled: true
        }
      },
      smooth: {
        enabled: false
      }
    },
    manipulation: {
      addNode: function (data, callback) {
        // filling in the popup DOM elements
        $node_operation[0].innerText = "Add Node";
        data.label = "";
        editNode(data, clearNodePopUp, callback);
      },
      editNode: function (data, callback) {
        // filling in the popup DOM elements
        $node_operation[0].innerText = "Edit Node";
        editNode(data, cancelNodeEdit, callback);
      },
      addEdge: function (data, callback) {
        if (data.from == data.to) {
          var r = confirm("Do you want to connect the node to itself?");
          if (r != true) {
            callback(null);
            return;
          }
        }
        $edge_operation[0].innerText = "Add Edge";
        editEdgeWithoutDrag(data, callback);
      },
      editEdge: {
        editWithoutDrag: function (data, callback) {
          $edge_operation[0].innerText = "Edit Edge";
          editEdgeWithoutDrag(data, callback);
        },
      }
    },
    physics: {
      enabled: false
    }
  };
  builder_network = new vis.Network(container, builder_network_data, options);
}

function builder_destroy() {
  if (builder_network !== null) {
    builder_network.destroy();
    builder_network = null;
  }
}

function builder_init() {
  builder_draw();
}

/* ------------------------------------------------------------------------ */
// Handle Query Toggle

$node_query.change(function () {
  const query = $node_query.prop('checked') == true;
  if (query) {
    $node_label.val('?');
    $node_label.prop('disabled', true);
  } else {
    $node_label.prop('disabled', false);
    $node_label.val('');
    $node_label.focus();
  }
});

$edge_query.change(function () {
  const query = $edge_query.prop('checked') == true;
  if (query) {
    $edge_label.selectpicker('val', null);
    $edge_label.prop('disabled', true);
  } else {
    $edge_label.prop('disabled', false);
    $edge_label.focus();
  }
});

/* ---------------------------- Edit Functions ---------------------------- */

// Node Edits

function editNode(data, cancelAction, callback) {
  if (data.label) {
    $node_label.val(data.label);
  }
  if (data.category) {
    $node_type.selectpicker('val', data.category);
  }
  if (data.query) {
    $node_query.prop('checked', data.query).change();
  }

  $node_save_button[0].onclick = saveNodeData.bind(this, data, callback);
  $node_cancel_button[0].onclick = cancelAction.bind(this, callback);

  $node_popup.show();
  $node_label.focus();
}

// Callback passed as parameter is ignored
function clearNodePopUp() {
  $node_label.val(null);
  $node_type.selectpicker('val', null);
  $node_query.prop('checked', false).change();
  $node_save_button[0].onclick = null;
  $node_cancel_button[0].onclick = null;
  $node_popup.hide();
}

function cancelNodeEdit(callback) {
  clearNodePopUp();
  callback(null);
}

function saveNodeData(data, callback) {
  data.label = $node_label.val().trim() || "?";
  data.category = $node_type.val();
  if (data.category) {
    data.title = data.category;
  }
  data.query = ($node_query.prop('checked') == true) || data.label == "?";

  console.log(data);
  clearNodePopUp();
  callback(data);
}

// Edge Edits

function editEdgeWithoutDrag(data, callback) {
  // filling in the popup DOM elements
  if (data.label) {
    $edge_label.val(data.label);
  }
  if (data.query) {
    $edge_query.prop('checked', data.query).change();
  }
  $edge_save_button[0].onclick = saveEdgeData.bind(this, data, callback);
  $edge_cancel_button[0].onclick = cancelEdgeEdit.bind(this, callback);

  $edge_popup.show();
  $edge_label.focus();
}

function clearEdgePopUp() {
  $edge_label.selectpicker('val', null);
  $edge_query.prop('checked', false).change();
  $edge_save_button[0].onclick = null;
  $edge_cancel_button[0].onclick = null;
  $edge_popup.hide();
}

function cancelEdgeEdit(callback) {
  clearEdgePopUp();
  callback(null);
}

function saveEdgeData(data, callback) {
  if (typeof data.to === "object") data.to = data.to.id;
  if (typeof data.from === "object") data.from = data.from.id;
  data.label = $edge_label.val();
  data.query = $edge_query.prop('checked') == true;

  console.log(data);
  clearEdgePopUp();
  callback(data);
}

/* --------------------------- Export Functions ---------------------------- */

function exportData() {
  var data = {
    nodes: [],
    edges: []
  };

  var idx = 0;
  for (const node of Object.values(builder_network.body.nodes)) {
    const node_id = ++idx;
    node.options.node_id = node_id;
    data.nodes.push({
      id: node_id,
      label: node.options.category || null,
      properties: {
        lemma: node.options.label,
        query: Boolean(node.options.query)
      }
    });
  }

  for (const edge of Object.values(builder_network.body.edges)) {
    const source_node = builder_network.body.nodes[edge.fromId];
    const target_node = builder_network.body.nodes[edge.toId];
    data.edges.push({
      source: source_node.options.node_id,
      target: target_node.options.node_id,
      label: edge.options.label || null,
      properties: {
        query: Boolean(edge.options.query)
      }
    })
  }
  console.log(data);
  return data;
}

/* ------------------------------------------------------------------------ */
