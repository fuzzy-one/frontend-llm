Ollama -> OpenSearch connector
================================

Files:
- `connector.py` - small Flask service that calls Ollama to get embeddings and indexes into OpenSearch.
- `requirements.txt` - Python deps.

Quick start (virtualenv):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OLLAMA_HOST=http://192.168.10.115:11434
export OLLAMA_MODEL=vladxpetrescu/labse:latest
export OPENSEARCH_HOST=https://192.168.40.101:9200
export OPENSEARCH_USER=admin
export OPENSEARCH_PASS=FaraParole69
python connector.py
```

Indexing example (call the connector directly):

```bash
curl -X POST "http://localhost:5000/embed" -H 'Content-Type: application/json' -d '{"id":"doc1","text":"this is a test","index":"documents"}'
```

Setup notes:
- The connector will create documents in the given index. The `embedding` field in these documents will be an array. For vector search, create an index with a `dense_vector` mapping (see `setup_opensearch.py` script if provided).
- To use as an ingest step, you can either call this connector from an OpenSearch ingest pipeline using the HTTP processor (if available), or call this connector from your ingestion workflow before sending documents to OpenSearch.
