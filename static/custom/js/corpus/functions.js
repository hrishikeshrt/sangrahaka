function response_handler(response) {
    $('#corpus-title').html(response.title);
    return response.data;
}

function generic_line_detail_formatter(index, row) {
    var html = [
        '<div class="table-responsive-sm"><table class="table table-striped">'
    ];

    var rows = {};
    if(!row.analysis) {
        html.push('<tr><td>No details available.</td></tr>');
    } else {
        var first_word = row.analysis[0];
        for (const k in first_word) {
            rows[k] = [];
        }
        for (const word of row.analysis) {
            for (const [k, v] of Object.entries(word)) {
                rows[k].push(v);
            }
        }
        for (const [name, data] of Object.entries(rows)) {
            html.push(`<tr><th scope="row">${name}</th><td>${data.join("</td><td>")}</td></tr>`);
        }
    }
    html.push('</table></div>')
    return html.join("\n");
}

function sanskrit_line_detail_formatter(index, row) {
    var words = [];
    var roots = [];
    var genders = [];
    var cases = [];
    var forms = [];
    var noun_markers = [];

    for (word of row.analysis) {
        words.push(word.original);
        roots.push(word.root);
        if (word.details !== {}) {
            genders.push(word.details.gender);
            cases.push(word.details.case);
            forms.push(word.details.form);
        } else {
            genders.push("");
            cases.push("");
            forms.push("");
        }
        noun_markers.push(word.is_noun);
    }

    var html = [
        '<div class="table-responsive-sm"><table class="table table-striped">',
        '<tr><th scope="row">Word</th><td>' + words.join("</td><td>") + '</td></tr>',
        '<tr><th scope="row">Root</th><td>' + roots.join("</td><td>") + '</td></tr>',
        '<tr><th scope="row">Gender</th><td>' + genders.join("</td><td>") + '</td></tr>',
        '<tr><th scope="row">Case</th><td>' + cases.join("</td><td>") + '</td></tr>',
        '<tr><th scope="row">Number</th><td>' + forms.join("</td><td>") + '</td></tr>',
        '<tr><th scope="row">Noun?</th><td>' + noun_markers.join("</td><td>") + '</td></tr>',
        '</table></div>',
    ];

    return html.join("\n");
}

function column_marked_formatter(value, row) {
    return value ? '<i class="fa fa-check"></i>' : '';
}

function entity_formatter(root, type, li_classes = "", annotator = "") {
    var entity_value = [root, type].join('$');
    var li_class = 'list-group-item';
    if (li_classes !== "") {
        li_class += " " + li_classes;
    }
    var entity_html = [
        annotator ? `<li title="${annotator}" class="${li_class}">` : `<li class="${li_class}">`,
        '<div class="row">',
        `<div class="col-sm-4">${root}</div>`,
        `<div class="col-sm-4 text-secondary">${type}</div>`,
        '<div class="col-sm-4">',
        '<span class="float-right">',
        `<input type="checkbox" name="entity" value="${entity_value}" class="mr-5"`,
        ' data-toggle="toggle" data-size="sm" data-on="<i class=\'fa fa-check\'></i>" ',
        ' data-off="<i class=\'fa fa-times\'></i>" data-onstyle="success"',
        ' data-offstyle="danger" checked>',
        '</span>',
        '</div>',
        '</div>',
        '</li>'
    ];
    return entity_html.join("");
}

function unnamed_formatter(line_id, text) {
    // 'unnamed_prefix' is a global constant
    // It must be set before running this function
    // It is set in corpus.html
    var upper_text = text.toUpperCase();
    var pattern = new RegExp('^'+ unnamed_prefix +'[0-9]$');
    if (upper_text.match(pattern)) {
        return upper_text + '-' + line_id;
    }
    return text;
}

function relation_formatter(source, label, target, detail, li_classes = "", annotator = "") {
    if (detail == null) {
        detail = "";
    }
    var relation_value = [source, label, target, detail].join('$');
    var li_class = 'list-group-item';
    if (li_classes !== "") {
        li_class += " " + li_classes;
    }
    var relation_html = [
        annotator ? `<li title="${annotator}" class="${li_class}">` : `<li class="${li_class}">`,
        '<div class="row">',
        '<div class="col-sm">',
        `(${source})`,
        ` <span class="text-muted">⊢ [${label} (${detail})] →</span> `,
        `(${target})`,
        '</div>',
        '<div class="col-sm-3">',
        '<span class="float-right">',
        `<input type="checkbox" name="relation" value="${relation_value}" class="mr-5"`,
        ' data-toggle="toggle" data-size="sm" data-on="<i class=\'fa fa-check\'></i>" ',
        ' data-off="<i class=\'fa fa-times\'></i>" data-onstyle="success"',
        ' data-offstyle="danger" checked>',
        '</span>',
        '</div>',
        '</div>',
        '</li>'
    ];
    return relation_html.join("");
}

function action_formatter(label, actor_label, actor, li_classes = "", annotator = "") {
    var action_value = [label, actor_label, actor].join('$');
    var li_class = 'list-group-item';
    if (li_classes !== "") {
        li_class += " " + li_classes;
    }
    var action_html = [
        annotator ? `<li title="${annotator}" class="${li_class}">` : `<li class="${li_class}">`,
        '<div class="row">',
        '<div class="col-sm">',
        `(${label})`,
        ` <span class="text-muted">⊢ [${actor_label}] →</span> `,
        `(${actor})`,
        '</div>',
        '<div class="col-sm-3">',
        '<span class="float-right">',
        `<input type="checkbox" name="action" value="${action_value}" class="mr-5"`,
        ' data-toggle="toggle" data-size="sm" data-on="<i class=\'fa fa-check\'></i>" ',
        ' data-off="<i class=\'fa fa-times\'></i>" data-onstyle="success"',
        ' data-offstyle="danger" checked>',
        '</span>',
        '</div>',
        '</div>',
        '</li>'
    ];
    return action_html.join("");
}

function row_attribute_handler(row, index) {
    return {}
}
