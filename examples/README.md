# Examples

Some minimal examples for,
* Preparing chapter files for upload
* Preparing knowledge graph from annotations
* Preparing query files

## Chapter File Structure

* A chapter file is a valid JSON containing list of objects.
* Every object corresponds to a line
* A line object has following keys,
    - `verse`: ID of the verse if applicable. (For prose corpora, this can increment with a line, or can be kept same for all lines.)
    - `text`: Text of the line, must be non-empty.
    - `split`: For languages which make heavy use of compounds and have a compound splitter available, a split version of text can be made available to aid human annotators
    - `analysis`: Analysis object
* Analysis object has the following keys,
    - `source`: Short keyword indicating the source (can be name of the tool or platform or any relevant string about how the analysis was obtained). This field can be empty.
    - `text`: Any textual representation of the analysis. This field can be empty.
    - `tokens`: A list of token objects.
* A token object can contain any keys. Only restriction is that all token objects must have the same schema.

e.g.

```
[
    {
        "verse": "1",
        "text": "First line of the text",
        "split": "",
        "analysis": {
            "souce": "manual",
            "text": "",
            "tokens": [
                {"Word": "First", "Lemma": "first", "k1": ""},
                {"Word": "line", "Lemma": "line", "k1": ""},
                {"Word": "of", "Lemma": "of", "k1": ""},
                {"Word": "the", "Lemma": "the", "k1": ""},
                {"Word": "text", "Lemma": "text", "k1": ""},
            ]
        }
    },
    ...

]
```

**NOTE**: Check out [epics/corpus/prepare.py](epics/corpus/prepare.py) to see how to convert
a plaintext into desired JSON format.

## Plaintext Corpus

One may also upload plaintext corpus, which will undergo regular-expression based
tokenization (verses split on `\n\n` and lines split on `\n` and words split on `\s`).

**NOTE**: Beware that such upload will lack `Analysis` fields.

## Preparing JSONL Graph

* `utils/propery_graph.py` implements a basic `PropertyGraph` class for the construction of knowledge graph and conversion to to JSONL format.
* It contains utility functions such as `add_node`, `add_edge` for adding nodes and edges.
* It implements `to_jsonl` utility function which can export the graph in JSON-Lines format, where each line is a valid JSON and corresponds to a Node or a Relation.
* Workflow is as follows,
    - Inherit the `PropertyGraph` class
    - Load nodes and relations from the annotation database
    - Add nodes using `add_node()` method and edges using `add_edge()` method.
    - Export the graph using `to_jsonl()` method.
* Method `infer` may be implemented as per need.
    - Used when an edge is added with at least one of the nodes absent
    - Should return `src_labels`, `dst_labels`, `src_properties` and `dst_properties`
* Custom custom functions to implement custom logic for preparing knowledge graph.
* `build_graph.py` files illustrate the workflow.

### Importing in Neo4j

Generated `.jsonl` file can be transferred to the import directory of Neo4j installation and directly imported in Neo4j graph databse through `apoc` module by using following command,

`call apoc.import.json("graph.jsonl")`

## Preparing Query File

Query file is a valid JSON file that contains a list of query objects.