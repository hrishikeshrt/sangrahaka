# Saṅgrāhaka

An easy and robust web-based distributed **Annotation and Querying Framework**.

This work has been accepted in ESEC/FSE 2021.

## Instructions

* Clone repository
* `pip install -r requirements.txt`
*  Install [Neo4j](https://neo4j.com/download-center/#community) (Required for querying)
    - Navigate to the `Neo4j` installation directory
    - Start Graph server `./bin/neo4j console`
* Copy `settings.sample.py` to `settings.py` and make appropriate changes.
* Run application server using `python3 server.py`
* Load the URL displayed on the terminal in the browser of your choice.
* Login using the administrator username and password set by you in `settings.py`
* Go to `Admin` tab to create a corpus and upload chapter files.
* Create `Ontology` in one of the two ways.
  - Use GUI to `Add` single relations.
  - Use `CSV` or `JSON` files to upload `Ontology` in bulk. (Check to [data/tables](data/tables) for file format and sample data)

Your Sangrahaka instance is now ready for annotation!

* Ask your annotators to create accounts on your system.
* Go to `Admin` tab to add `Annotator` role to the desired users.


**Note**: `examples` directory contains sample files for corpus creation, query template and graph building.

## Demo

* Presentation: https://hrishikeshrt.github.io/publication/fse2021/presentation.mp4


## Cite

```
@inproceedings{terdalkar2021sangrahaka,
author = {Terdalkar, Hrishikesh and Bhattacharya, Arnab},
title = {Sangrahaka: A Tool for Annotating and Querying Knowledge Graphs},
year = {2021},
isbn = {9781450385626},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3468264.3473113},
doi = {10.1145/3468264.3473113},
booktitle = {Proceedings of the 29th ACM Joint Meeting on European Software Engineering Conference and Symposium on the Foundations of Software Engineering},
pages = {1520–1524},
numpages = {5},
keywords = {Querying Tool, Knowledge Graph, Annotation Tool},
location = {Athens, Greece},
series = {ESEC/FSE 2021}
}
```

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


