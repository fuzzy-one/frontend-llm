# Agents Index - MVP Setup

## Create Index

```bash
curl -X PUT "https://192.168.40.101:9200/agents" \
  -u admin:FaraParole69 \
  -k \
  -H "Content-Type: application/json" \
  -d '{
  "mappings": {
    "properties": {
      "phone": { "type": "keyword" },
      "type": { "type": "keyword" },
      "agency_name": { 
        "type": "text",
        "fields": {
          "keyword": { "type": "keyword" }
        }
      },
      "source": { "type": "keyword" },
      "scraped_at": { "type": "date" },
      "ad_count": { "type": "integer" }
    }
  }
}'
```

## Sample Data

```bash
# Bulk insert agents
curl -X POST "https://192.168.40.101:9200/agents/_bulk" \
  -u admin:FaraParole69 \
  -k \
  -H "Content-Type: application/x-ndjson" \
  -d '
{"index": {"_id": "0722123456"}}
{"phone": "0722123456", "type": "agent", "agency_name": "Imobiliare XYZ", "source": "scraped", "ad_count": 45}
{"index": {"_id": "0733987654"}}
{"phone": "0733987654", "type": "agency", "agency_name": "RE/MAX Romania", "source": "scraped", "ad_count": 120}
'
```

## Cross-Index Lookup (Option A: Application-side)

```python
def enrich_with_agent_info(results: list, os_client) -> list:
    """Add is_agency flag by looking up phones in agents index"""
    
    # Collect all phones from results
    phones = [r.get('phone') for r in results if r.get('phone')]
    phones = [p for p in phones if p and p != 'N/A']
    
    if not phones:
        return results
    
    # Batch lookup in agents index
    query = {
        "query": {
            "terms": {"phone": phones}
        },
        "_source": ["phone", "type", "agency_name"]
    }
    
    response = os_client.search(index="agents", body=query)
    
    # Build lookup dict
    agent_lookup = {}
    for hit in response['hits']['hits']:
        src = hit['_source']
        agent_lookup[src['phone']] = {
            'is_agency': True,
            'seller_type': src.get('type', 'agent'),
            'agency_name': src.get('agency_name')
        }
    
    # Enrich results
    for result in results:
        phone = result.get('phone')
        if phone in agent_lookup:
            result.update(agent_lookup[phone])
        else:
            result['is_agency'] = False
            result['seller_type'] = 'private'
    
    return results
```

## Cross-Index Search (Option B: OpenSearch Terms Lookup)

OpenSearch supports terms lookup from another index:

```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"description": "apartament 2 camere"}}
      ],
      "must_not": [
        {
          "terms": {
            "decrypted_phone": {
              "index": "agents",
              "path": "phone"
            }
          }
        }
      ]
    }
  }
}
```

⚠️ This requires the agents index to be small and have all phones. Better to do application-side lookup for flexibility.
