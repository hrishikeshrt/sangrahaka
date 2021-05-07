# Saṅgrāhaka

An easy and robust web-based distributed **Annotation and Querying Framework**.

## Instructions

* Clone repository
* `pip install -r requirements.txt`
*  Install [Neo4j](https://neo4j.com/download-center/#community) (Optional. Required for querying)
    - Navigate to the `Neo4j` installation directory
    - Start Graph server `./bin/neo4j console`
* Copy `settings.sample.py` to `settings.py` and make appropriate changes.
* Run application server `python server.py`

**Note**: `examples` directory contains sample files for corpus creation, query template and graph building.

## Structure

```
.
├── requirements.txt
├── models_sqla.py
├── server_sqla.py
├── server.py -> server_sqla.py
├── settings.sample.py
├── examples
│   ├── README.md
│   └── epics
│       ├── corpus
│       ├── query.json
│       ├── build_graph.py
│       └── README.md
├── utils
│   ├── configuration.py
│   ├── graph.py
│   ├── property_graph.py
│   ├── query.py
│   └── reverseproxied.py
├── templates
│   ├── about.html
│   ├── admin.html
│   ├── contact.html
│   ├── corpus.html
│   ├── entity.html
│   ├── footer.html
│   ├── header.html
│   ├── home.html
│   ├── macros.html
│   ├── messages.html
│   ├── privacy.html
│   ├── query.html
│   ├── relation.html
│   ├── security
│   │   ├── change_password.html
│   │   ├── email
│   │   ├── forgot_password.html
│   │   ├── login_user.html
│   │   ├── register_user.html
│   │   └── reset_password.html
│   ├── settings.html
│   └── terms.html
├── static
│   ├── bootstrap
│   ├── css
│   ├── custom
│   │   ├── css
│   │   └── js
│   │       ├── corpus
│   │       │   ├── elements.js
│   │       │   ├── events.js
│   │       │   └── functions.js
│   │       └── query
│   │           ├── network.js
│   │           └── query.js
│   ├── fontawesome
│   ├── js
│   ├── plugins
│   │   ├── bootstrap-table
│   │   ├── css
│   │   │   ├── animate.min.css
│   │   │   ├── bootstrap4-toggle.min.css
│   │   │   └── bootstrap-select.min.css
│   │   └── js
│   │       ├── bootstrap4-toggle.min.js
│   │       ├── bootstrap-autocomplete.min.js
│   │       ├── bootstrap-notify.min.js
│   │       ├── bootstrap-select.min.js
│   │       ├── tableExport.min.js
│   │       └── vis-network.min.js
│   └── themes
├── scripts
│   ├── build_graph.py
│   ├── build_query_file.py
│   └── convert_sheet_annotations.py
└── README.md
```


