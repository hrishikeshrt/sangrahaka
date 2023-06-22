# Installation Instructions

Saṅgrāhaka is presented as a full-stack application that you can install on your
own server. Installing it is fairly straightforward if you have the necessary
components.

## Requirements

Saṅgrāhaka makes use of cross-platform technologies, and in theory should
run on all operating systems. It has been tested and is known to work on Ubuntu
18.04 and Windows.

### Primary Requirements

* [Python3](https://www.python.org/downloads/): First and foremost, being powered by [Flask](https://flask.palletsprojects.com/en/2.2.x/), Saṅgrāhaka requires Python 3.
  - Tested on Python 3.8.
  - You may want to use [Anaconda](https://docs.anaconda.com/free/anaconda/install/).
* Several features of Saṅgrāhaka are made possible through use of numerous Python packages available on the [Python Package Index (PyPI)](https://pypi.org/).
  - Install them using `pip install -r requirements.txt`

### Secondary Requirements

*  [Neo4j](https://neo4j.com/download-center/#community) is a graph database management system (Think MySQL but for graphs!). Saṅgrāhaka uses Neo4j as its graph database to store and query knowledge graphs.
  - Check the installation instructions for your platform.
  - **Note**: Annotation process does not require Neo4j. Therefore, if you want to quickly get started with annotation without worrying about knowledge graphs, you can skip installing Neo4j.
  - **Caution**: The interfaces under `Graph` tab will not function if a graph database is not connected.

## Core Setup

### Start Web (Flask) Server

* Configure the application.
  - Copy `settings.sample.py` to `settings.py`
  - Open `settings.py` in a text editor and make appropriate changes.
* Run application server.
  - Open a terminal.
  - Run `python3 server.py`
  - **Note**: If you want to run it on a production environment, it is recommended to use a Web Server Gateway Interface (WSGI) such as [Gunicorn](https://gunicorn.org/)
* Access the frontend to start using
  - Copy the URL displayed on the terminal and load it in the browser of your choice.

Your Saṅgrāhaka instance is now running!

## Annotation Setup

### Setup Annotation Task

* Login using the administrator username and password set by you in `settings.py`
* Go to `Admin` tab.
* Upload Corpus
  - Create a corpus entry by providing a name and an optional description.
  - Prepare chapter files. (Check [examples](examples/) directory for the format of chapter files.)
  - Upload chapter files.
* Create Ontology
  - Prepare a list of node types relevant to your corpus.
  - Prepare a list of relationships that you want to capture among these node types.
  - Upload the ontology in one of the two ways:
    - Use GUI to `Add` relations one by one.
    - Use `CSV` or `JSON` files to upload `Ontology` in bulk. (Check to [data/tables](data/tables) for file format and sample data.)

Your Saṅgrāhaka instance is now ready for annotation!

### Start Annotation

* Ask your annotators to create accounts on your system.
* Go to `Admin` tab to add `Annotator` role to the desired users.

## Querying Setup

### Build Knowledge Graph

The knowledge graph needs to be constructed using the collected annotations.
The `PropertyGraph()` class provided in [`utils/property_graph.py`](utils/property_graph.py) can be used for this purpose.

**Note**: [`examples`](examples/) directory contains sample files for building the knowledge graph.

**Disclaimer**: This step requires some level of familiarity with Python and computational aspects.

### Prepare Query Templates

Query templates should be prepared at `data/query.json`. The format of query templates as well as sample
files highlighting the query template preparation are available in [`examples`](examples/).

**Disclaimer**: This step requires some level of familiarity with Cypher and computational aspects.

### Start Graph Database (Neo4j) Server *(optional)*

If you have installed Neo4j and want to use graph related features, you should
start a graph database server. It need not be on the same machine as the web
server, but it needs to be accessible via network to the machine hosting your
web server.

* Start Neo4j graph server
  - Open a terminal.
  - Navigate to the `Neo4j` installation directory. (`cd <your-neo4j-installation-path>`)
  - Run `./bin/neo4j console`

**Note**: The graph server should be started before starting the web server. If you have already
started the web server, you can always stop it and restart it.
