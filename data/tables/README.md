# Tables

* This folder contains sample data to illustrate format of various tables.
* File name should be `table_name.json` or `table_name.csv`
* Please refer to `sample/` directory for examples.
* The files can be uploaded through Admin tab for bulk ontology update.

## Schema

* **JSON**: `List[Dict[str, str]]`: Mandatory keys as per schema
* **CSV**: Mandatory columns as per schema

* Label Tables (`node_label.json`, `relation_label.json`, `action_label.json`, `actor_label.json`)
  - `label`
  - `description`
