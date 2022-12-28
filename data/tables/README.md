# Tables

* This folder contains data to initialize various tables on the first run.
* File name should be `table_name.json` or `table_name.csv`
  - If both are present, `.json` takes priority over `.csv`
* Please refer to `sample/` directory for examples.

## Schema

* **JSON**
  - Files: `node_label.json`, `relation_label.json`, `action_label.json`, `actor_label.json`
  - Format: `List[Dict[str, str]]`
  - Mandatory Keys: `label`, `description`
* **CSV**
  - Files: `node_label.csv`, `relation_label.csv`, `action_label.csv`, `actor_label.csv`
  - Mandatory Columns: `label`, `description`

