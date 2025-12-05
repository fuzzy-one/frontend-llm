# Agent Detection Strategy

## Detection Signals

### 1. High Volume (40-60 points)
- 5+ active ads from same phone: +40 points
- 10+ active ads from same phone: +60 points

### 2. Keywords (20 points)
```python
AGENT_KEYWORDS = [
    'agentie', 'agenție', 'imobiliar', 'imobiliare',
    'consultant', 'broker', 'agent',
    'alte oferte', 'portofoliu', 'vezi toate',
    'colaborare', 'comision', 'exclusivitate'
]
```

### 3. Multi-Platform (20 points)
- Same phone on 3+ platforms: +20 points

### 4. Known Agent List (100 points)
- Manual blacklist: instant 100 points

## Scoring Thresholds

| Score | Classification |
|-------|---------------|
| 70+ | Agent (confirmed) |
| 40-69 | Suspected Agent |
| 0-39 | Private Seller |

## Agent Detection Job (Future)

```python
def detect_agents(os_client):
    """Run agent detection on all sellers"""
    
    # Aggregate ads by phone
    agg_query = {
        "size": 0,
        "aggs": {
            "by_phone": {
                "terms": {
                    "field": "phone",
                    "size": 10000,
                    "min_doc_count": 3
                },
                "aggs": {
                    "sources": {
                        "terms": {"field": "source"}
                    },
                    "avg_price": {
                        "avg": {"field": "current_price"}
                    }
                }
            }
        }
    }
    
    result = os_client.search(index="properties", body=agg_query)
    
    for bucket in result['aggregations']['by_phone']['buckets']:
        phone = bucket['key']
        ad_count = bucket['doc_count']
        source_count = len(bucket['sources']['buckets'])
        
        agent_score = 0
        signals = []
        
        if ad_count >= 10:
            agent_score += 60
            signals.append('high_volume_10plus')
        elif ad_count >= 5:
            agent_score += 40
            signals.append('high_volume_5plus')
        
        if source_count >= 3:
            agent_score += 20
            signals.append('multi_platform')
        
        # Determine type
        if agent_score >= 70:
            seller_type = 'agent'
        elif agent_score >= 40:
            seller_type = 'suspected_agent'
        else:
            seller_type = 'private'
        
        # Upsert seller
        seller_doc = {
            'seller_id': phone,
            'phones': [phone],
            'type': seller_type,
            'confidence': min(agent_score / 100, 1.0),
            'detection_signals': signals,
            'total_listings': ad_count,
            'avg_price': bucket['avg_price']['value']
        }
        
        os_client.index(index='sellers', id=phone, body=seller_doc)
```

## MVP Implementation (Now)

For MVP, just use a simple `agents` index with known phones:

```json
// agents index - simple lookup
{
  "phone": "0722123456",
  "type": "agent",
  "agency_name": "Imobiliare XYZ",
  "source": "scraped"  // or "manual"
}
```

Then cross-index lookup during search to flag results.
