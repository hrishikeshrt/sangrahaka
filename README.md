# Saṅgrāhaka

An easy and robust web-based distributed **Annotation and Querying Framework**.

This work has been accepted in [ESEC/FSE 2021](https://2021.esec-fse.org/).

## Install

Saṅgrāhaka is presented as a full-stack application that you can install on your own server.

The detailed installation instructions are available at [INSTALL.md](INSTALL.md).

### Basic Setup

* Clone (or Download) this repository.
* `pip install -r requirements.txt`
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

### Graph Setup

*  Install [Neo4j](https://neo4j.com/download-center/#community) (Required for querying)
  - Navigate to the `Neo4j` installation directory
  - Start the graph server: `./bin/neo4j console`
* Construct the knowledge graph.
* Load the knowledge graph into Neo4j.
* Prepare the query templates file and place it in the `data/` folder.
* Restart web server.

**Disclaimer**: Steps such as preparing corpus files, query templates building knowledge graph requires
a certain level of familiarity with programming and the computational aspects.

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
├── settings.sample.py
├── models_admin.py
├── models_sqla.py
├── server.py -> server_sqla.py
├── server_sqla.py
├── constants.py
├── data
│   ├── query.json
│   └── tables
│       ├── README.md
│       └── sample
├── db
│   ├── main.db
│   └── README.md
├── templates [*.html]
├── utils
│   ├── configuration.py
│   ├── cypher_utils.py
│   ├── database.py
│   ├── graph.py
│   ├── plaintext.py
│   ├── property_graph.py
│   ├── query.py
│   └── reverseproxied.py
├── static
│   ├── audio [...]
│   ├── bootstrap [...]
│   ├── css [...]
│   ├── custom
│   │   ├── css
│   │   │   ├── builder
│   │   │   │   ├── builder.css
│   │   │   │   └── [...]
│   │   │   └── sticky-footer.css
│   │   └── js
│   │       ├── admin
│   │       │   └── admin.js
│   │       ├── browse
│   │       │   └── browse.js
│   │       ├── builder
│   │       │   └── builder.js
│   │       ├── corpus
│   │       │   ├── annotation.js
│   │       │   ├── curation.js
│   │       │   ├── elements.js
│   │       │   ├── events.js
│   │       │   └── functions.js
│   │       └── query
│   │           ├── network.js
│   │           └── query.js
│   ├── fontawesome [...]
│   ├── images [...]
│   ├── js [...]
│   ├── plugins [...]
│   └── themes [...]
├── examples
│   ├── ayurveda [...]
│   ├── epics [...]
│   ├── README.md
│   └── requirements.txt
├── output [...]
├── explore_database.py
├── setup.cfg
├── INSTALL.md
└── README.md
```