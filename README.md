# Log Intelligence System

A Python log severity classification pipeline that combines deterministic regex rules, an embedding-based ML classifier, an in-memory vector cache, and an LLM fallback. The project is organized around a LangGraph workflow that classifies raw log lines into severity labels such as `INFO`, `WARNING`, `ERROR`, and `CRITICAL`.

The codebase currently behaves like a local CLI/research project rather than a web service: there are no API route files, database migrations, Dockerfiles, or deployment manifests in the repository.

## Workflow Architecture

The main runtime entry point is `main.py`. It creates a blank `LogState`, invokes the compiled LangGraph workflow from `graph/graph.py`, and prints the final severity classification.

```text
Raw log line
    |
    v
main.py
    |
    v
blank_state(log) -> LogState
    |
    v
LangGraph workflow: graph/graph.py
    |
    v
regex_node
    |-- regex match found -------------------------> final_node -> result
    |
    v
ml_node
    |-- ml_confidence >= 0.85 ---------------------> final_node -> result
    |
    v
vector_search_node
    |-- vector_score >= 0.90 ----------------------> final_node -> result
    |
    v
llm_node
    |
    v
validate_node
    |-- valid response ----------------------------> save_to_vector_node -> final_node -> result
    |-- invalid and attempts < 3 ------------------> llm_node
    |-- invalid and attempts exhausted ------------> save_to_vector_node -> final_node -> result
```

### Runtime Classification Flow

- **Input creation**
  - `main.py` accepts a raw log string in the `classify(log)` function.
  - `blank_state(log)` creates the shared graph state with fields for regex, ML, vector search, LLM, validation, and final output.
  - The state type is defined in `graph/state.py` as `LogState`.

- **Graph orchestration**
  - `graph/graph.py` builds a LangGraph `StateGraph`.
  - The graph entry point is `regex_node`.
  - Conditional edges in `nodes/router.py` decide whether the workflow can stop early or must continue to the next classifier.

- **Phase 1: Regex classification**
  - `nodes/regex_node.py` calls `RegexEngine` from `regex_method/regex_engine.py`.
  - `RegexEngine` compiles patterns from `regex_method/regex_rules.py`.
  - A matched rule returns a severity label, confidence, and `classified_by="regex"`.
  - If a regex label is found, the workflow goes directly to `final_node`.
  - This is the fastest and most deterministic path.

- **Phase 2: ML classification**
  - `nodes/ml_node.py` prepares the raw log with `utils.clean.prepare_for_ml`.
  - Cleaning first normalizes regex-sensitive noise, then applies deeper ML-oriented text cleanup.
  - The cleaned text is embedded with SentenceTransformer `all-MiniLM-L6-v2`.
  - A persisted scikit-learn classifier predicts the severity label.
  - If `ml_confidence >= 0.85`, the workflow accepts the ML result and goes to `final_node`.
  - If confidence is lower, the workflow continues to vector search.

- **Phase 3: Vector cache retrieval**
  - `nodes/vector_search_node.py` searches the in-memory FAISS index managed by `utils/vector_db.py`.
  - Vectors are normalized and searched with `faiss.IndexFlatIP`, which is used as cosine-style similarity.
  - If the best cached match has `vector_score >= 0.90`, the cached label is accepted.
  - If no strong cache hit exists, similar logs are passed forward as context for the LLM.

- **Phase 4: LLM fallback**
  - `nodes/llm_node.py` calls the Groq model configured in `utils/llm.py`.
  - The prompt includes:
    - the cleaned log text
    - valid labels
    - the ML model suggestion and confidence
    - similar logs from the vector cache when available
  - The LLM must return JSON with a `label` and a specific `reason`.
  - Invalid labels are rejected in Python before validation succeeds.

- **Phase 5: Validation and retry**
  - `nodes/validate_node.py` checks the LLM response.
  - Hard checks verify that the label exists, belongs to the allowed label set, and has a non-empty reason.
  - A second LLM judge checks whether the reason is consistent with the selected label and log.
  - The workflow retries `llm_node` until validation passes or `MAX_ATTEMPTS = 3` is reached.

- **Phase 6: Vector cache update**
  - `nodes/save_to_vector_node.py` stores validated LLM classifications in the FAISS vector cache.
  - Stored values include the cleaned text, embedding, and final label.
  - If the LLM path fails after all retries, the node falls back to the ML label when possible.
  - The cache is in-memory only and is reset when the Python process restarts.

- **Phase 7: Final resolution**
  - `nodes/final_node.py` resolves the final label, source, and reason.
  - It prioritizes explicit final values set by previous nodes.
  - If needed, it derives the final result from regex, ML, vector, or LLM state fields.
  - As a last resort, it defaults to `INFO` with source `fallback`.

### Data Preparation Workflow

```text
data/raw/<source>/*.log
    |
    v
preprocess.py
    |
    v
source adapter from adapters/
    |
    v
unified log records
    |
    v
data/processed/unified_logs.ndjson
```

- `preprocess.py` scans `data/raw`.
- Each subdirectory name is treated as a source, such as `apache`, `linux`, `mac`, `hdfs`, or `bgl`.
- Registered adapters parse known log formats into a common dictionary schema.
- If parsing fails inside a registered adapter, the generic adapter is used as a safety fallback.
- The unified output is written as newline-delimited JSON.

### Regex and ML Dataset Workflow

```text
unified logs / raw source logs
    |
    v
regex_method/dataset_cleaner.py
    |
    |-- regex matched -------> regex_classified.csv
    |
    |-- regex unmatched -----> ml_training.csv
```

- `regex_method/dataset_cleaner.py` parses known datasets and runs the regex engine.
- Regex-classified records are separated from records that need ML training.
- `regex_method/run_regex.py` can also run regex classification over `data/processed/unified_logs.ndjson`.
- `model/model_training.py` trains an embedding-based classifier from CSV data.
- The runtime loader expects a classifier and label encoder artifact, configured by environment variables or default paths.

### Pattern Mining Workflow

```text
unlabeled logs
    |
    v
SentenceTransformer embeddings
    |
    v
DBSCAN clustering
    |
    v
candidate repeated patterns
    |
    v
new regex rules can be added manually
```

- `analysis/dbscan_pattern_mining.py` clusters repeated unlabeled log messages.
- DBSCAN is used to identify frequent semantic groups.
- Output clusters are intended to help discover candidates for future regex rules.
- The script supports the project goal of moving repeated, high-confidence cases from LLM/ML handling into deterministic regex handling.

### State and Decision Fields

- `log`: original raw log string.
- `clean_text`: cleaned log used for embedding and LLM prompts.
- `log_vector`: SentenceTransformer embedding for the cleaned log.
- `regex_label`: label found by regex rules, if any.
- `ml_label` and `ml_confidence`: classifier prediction and probability.
- `vector_label`, `vector_score`, and `vector_context`: vector cache result and similar logs.
- `llm_response`: JSON-like LLM classification result.
- `validation_passed` and `validation_feedback`: validation result for the LLM path.
- `final_label`, `final_source`, and `final_reason`: resolved output returned to callers.
- `attempts`: number of LLM attempts made during the current classification.

### Routing Rules

- Accept regex immediately when `regex_label` exists.
- Accept ML when `ml_confidence >= 0.85`.
- Accept vector cache when `vector_score >= 0.90`.
- Use the LLM only when regex, ML, and vector cache do not produce a confident result.
- Retry the LLM path while validation fails and `attempts < MAX_ATTEMPTS`.
- Save LLM-path results to the vector cache before finalizing.

## Folder Structure

```text
.
├── main.py                    # CLI/demo entry point for classification
├── preprocess.py              # Converts raw source logs into unified NDJSON
├── requirements.txt           # Python dependencies
├── adapters/                  # Source-specific log parsers
├── graph/                     # LangGraph state and graph definition
├── nodes/                     # Classification workflow nodes
├── regex_method/              # Regex rules, regex engine, dataset split utilities
├── utils/                     # Cleaning, model loading, LLM, and vector DB helpers
├── model/                     # Local trained model artifacts and training notebook/script
├── analysis/                  # Research notebooks and DBSCAN pattern mining
└── data/                      # Local raw/processed datasets; ignored by git
```

## Core Modules

- `adapters/`: normalizes logs from Apache, Linux, macOS, HDFS, and BGL into a shared schema with fields such as `source`, `raw_log`, `clean_message`, `log_level`, `service`, `timestamp`, and `structured_fields`.
- `preprocess.py`: walks `data/raw/<source>/`, applies the matching adapter, and writes unified NDJSON to `data/processed/unified_logs.ndjson`.
- `regex_method/regex_engine.py`: compiles `REGEX_RULES` once and returns a severity level when a rule matches the cleaned message and source.
- `utils/clean.py`: provides separate cleaning paths for regex matching and ML embeddings.
- `utils/loader.py`: loads the persisted classifier, label encoder, and SentenceTransformer embedding model.
- `utils/vector_db.py`: wraps FAISS `IndexFlatIP` for normalized cosine-style similarity search. This cache is process-local and not persisted.
- `utils/llm.py`: creates a Groq chat model using `GROQ_API_KEY`.
- `graph/graph.py`: wires the LangGraph nodes and conditional routing.
- `nodes/`: contains the executable steps for regex classification, ML prediction, vector retrieval, LLM fallback, validation, cache insertion, and final resolution.

## Setup

Use Python 3.11 if possible, since the checked-in virtual environment metadata indicates Python 3.11 was used locally.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
ML_MODEL_PATH=model/svm_classifier.pkl
LABEL_ENCODER_PATH=model/label_encoder.pkl
```

`ML_MODEL_PATH` and `LABEL_ENCODER_PATH` are optional if you use the default filenames above. The model files are ignored by git, so a fresh clone needs compatible artifacts before `main.py` can run.

## Development Workflow

Preprocess raw logs:

```bash
python preprocess.py
```

Run the local classifier demo:

```bash
python main.py
```

Run regex classification over unified logs:

```bash
cd regex_method
python run_regex.py
```

Split datasets into regex-classified and ML-training CSVs:

```bash
cd regex_method
python dataset_cleaner.py
```

Train or experiment with models:

```bash
cd model
python model_training.py
```

Note: `model/model_training.py` currently saves `log_classifier.pkl` and `label_mapping.pkl`, while the runtime loader expects `model/svm_classifier.pkl` and `model/label_encoder.pkl` by default. Either rename/export compatible artifacts or override the paths with environment variables.

## Environment Variables

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `GROQ_API_KEY` | Required for LLM fallback and validation | None | API key used by `langchain-groq` |
| `ML_MODEL_PATH` | Optional | `model/svm_classifier.pkl` | Path to the scikit-learn classifier, relative to project root |
| `LABEL_ENCODER_PATH` | Optional | `model/label_encoder.pkl` | Path to the label encoder, relative to project root |

## Data and Models

The repository is configured to ignore `data/`, `*.csv`, `.env`, and `*.pkl` files. The local workspace contains raw datasets, processed outputs, and model artifacts, but these should be treated as external runtime assets.

Expected raw data layout:

```text
data/raw/
├── apache/
├── bgl/
├── hdfs/
├── linux/
├── mac/
└── thunderbird/
```

`preprocess.py` only processes subdirectories registered in its `ADAPTERS` mapping. Unknown sources fall back to `GenericAdapter` only when a source key is requested directly through `process_file`.

## Deployment

No deployment configuration is currently present. To deploy this project, package it as a Python process and provide:

- installed dependencies from `requirements.txt`
- `GROQ_API_KEY`
- trained classifier and label encoder artifacts
- access to the SentenceTransformer model `all-MiniLM-L6-v2`
- any required raw or processed data files

Because the FAISS vector cache is in-memory, cached LLM classifications are lost when the process restarts. Persisting FAISS indexes and metadata would be needed for durable production caching.

## Implementation Notes

- The most frequently changed tracked files include `nodes/ml_node.py`, `utils/loader.py`, `requirements.txt`, `preprocess.py`, `nodes/router.py`, `graph/state.py`, and the regex engine/rule files.
- `main.py` demonstrates classification with hard-coded sample logs; it is not currently an argparse-based CLI.
- The runtime graph imports the ML model and embedding model at module import time, so missing model files or unavailable embedding downloads will fail early.
- Regex rules are source-aware when parsed log objects include `source`. If a raw string is classified directly through `main.py`, `regex_node` supplies an empty source, and the regex engine evaluates rules without source filtering.
- `analysis/` contains notebooks and `dbscan_pattern_mining.py` for discovering repeated unlabeled patterns that may be promoted into regex rules.
- There is no persistent database layer. FAISS is used only as an in-memory vector index.
