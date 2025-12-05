# Deduplication Strategy

## Problem

Same property listed on multiple platforms:
- OLX
- Imobiliare.ro
- Storia.ro
- Publi24
- Romimo

Agents cross-post from their CRM. Private sellers also multi-list.

## Detection Signals

### 1. Exact Match
- Same `ad_id` + `source` = same listing (update version)

### 2. Phone + Address Match (+60% confidence)
- Same phone number
- Similar address (fuzzy match)
- Same room count

### 3. Image Hash Match (+30% confidence)
- Perceptual hash (pHash) of images
- Similarity > 90% = same property

### 4. Text Similarity (+20% confidence)
- Title + description embedding
- Cosine similarity > 0.95 = candidate

### 5. Geo + Attributes (+20% confidence)
- Coordinates within 50m
- Same rooms
- Price within 10%

## Confidence Scoring

| Signal | Points |
|--------|--------|
| Phone match | +40% |
| Image hash match | +30% |
| Address match | +20% |
| Price within 5% | +10% |
| Rooms match | +10% |

**If confidence > 80%, merge into same property**

## Implementation (Future)

```python
import hashlib
from imagehash import phash
from PIL import Image
import requests
from io import BytesIO

def compute_content_hash(ad: dict) -> str:
    """Hash for detecting content changes"""
    content = f"{ad.get('title', '')}|{ad.get('description', '')}|{ad.get('price', '')}"
    return hashlib.md5(content.encode()).hexdigest()

def compute_image_hash(image_url: str) -> str:
    """Perceptual hash for image dedup"""
    try:
        response = requests.get(image_url, timeout=5)
        img = Image.open(BytesIO(response.content))
        return str(phash(img))
    except:
        return None

def find_duplicate_candidates(new_ad: dict, os_client) -> list:
    """Find potential duplicates for a new ad"""
    candidates = []
    
    # Strategy 1: Same phone
    if new_ad.get('phone'):
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"seller_id": new_ad['phone']}},
                        {"term": {"status": "active"}}
                    ],
                    "filter": [
                        {"term": {"rooms": new_ad.get('rooms', 0)}},
                        {"range": {"current_price": {
                            "gte": new_ad['price'] * 0.9,
                            "lte": new_ad['price'] * 1.1
                        }}}
                    ]
                }
            }
        }
        # execute and score...
    
    # Strategy 2: Image hash match
    if new_ad.get('image_hashes'):
        query = {
            "query": {
                "terms": {"image_hashes": new_ad['image_hashes'][:3]}
            }
        }
        # execute and score...
    
    # Strategy 3: Location + attributes
    if new_ad.get('coordinates'):
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"rooms": new_ad.get('rooms')}},
                        {"term": {"transaction_type": new_ad.get('transaction_type')}}
                    ],
                    "filter": {
                        "geo_distance": {
                            "distance": "100m",
                            "coordinates": new_ad['coordinates']
                        }
                    }
                }
            }
        }
        # execute and score...
    
    return candidates

def merge_listings(property_doc: dict, new_listing: dict) -> dict:
    """Merge a new listing into existing property"""
    
    existing_sources = {l['source']: l for l in property_doc.get('listings', [])}
    
    if new_listing['source'] in existing_sources:
        # Update existing
        existing_sources[new_listing['source']].update({
            'last_seen': new_listing['scraped_at'],
            'price': new_listing['price'],
            'url': new_listing['url']
        })
    else:
        # Add new source
        property_doc['listings'].append({
            'source': new_listing['source'],
            'ad_id': new_listing['ad_id'],
            'url': new_listing['url'],
            'price': new_listing['price'],
            'last_seen': new_listing['scraped_at'],
            'is_primary': False
        })
    
    property_doc['last_seen'] = new_listing['scraped_at']
    
    return property_doc
```

## UI Result (Future)

```json
{
  "property_id": "prop-uuid-123",
  "title": "Apartament 2 camere Titan",
  "price": 95000,
  "listings": [
    {"source": "olx", "url": "https://olx.ro/..."},
    {"source": "imobiliare.ro", "url": "https://imobiliare.ro/..."},
    {"source": "storia.ro", "url": "https://storia.ro/..."}
  ],
  "listing_count": 3
}
```

Show "View on 3 sites" button in UI.
