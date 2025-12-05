# Index Schemas (Future)

## 1. Raw Ads Index (Versioned)

```json
// PUT real-estate-raw-2025.12
{
  "mappings": {
    "properties": {
      "ad_id": { "type": "keyword" },
      "source": { "type": "keyword" },
      "scraped_at": { "type": "date" },
      "version": { "type": "integer" },
      "content_hash": { "type": "keyword" },
      "price": { "type": "float" },
      "currency": { "type": "keyword" },
      "title": { "type": "text" },
      "description": { "type": "text" },
      "phone": { "type": "keyword" },
      "location_1": { "type": "keyword" },
      "location_2": { "type": "keyword" },
      "coordinates": { "type": "geo_point" },
      "images": { "type": "keyword" },
      "image_hashes": { "type": "keyword" },
      "attributes": { "type": "object" },
      "raw_html": { "type": "text", "index": false }
    }
  }
}
```

## 2. Canonical Properties Index

```json
// PUT properties
{
  "mappings": {
    "properties": {
      "property_id": { "type": "keyword" },
      "canonical_title": { "type": "text" },
      "description": { "type": "text" },
      "description_embedding": { 
        "type": "knn_vector", 
        "dimension": 1024,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesimil",
          "engine": "lucene"
        }
      },
      
      "current_price": { "type": "float" },
      "currency": { "type": "keyword" },
      "status": { "type": "keyword" },
      
      "location_1": { "type": "keyword" },
      "location_2": { "type": "keyword" },
      "coordinates": { "type": "geo_point" },
      "address_normalized": { "type": "keyword" },
      
      "transaction_type": { "type": "keyword" },
      "property_type": { "type": "keyword" },
      "rooms": { "type": "integer" },
      
      "listings": {
        "type": "nested",
        "properties": {
          "source": { "type": "keyword" },
          "ad_id": { "type": "keyword" },
          "url": { "type": "keyword" },
          "price": { "type": "float" },
          "last_seen": { "type": "date" },
          "is_primary": { "type": "boolean" }
        }
      },
      
      "price_history": {
        "type": "nested",
        "properties": {
          "date": { "type": "date" },
          "price": { "type": "float" },
          "source": { "type": "keyword" }
        }
      },
      "price_trend": { "type": "keyword" },
      "price_drop_pct": { "type": "float" },
      
      "seller_id": { "type": "keyword" },
      "seller_type": { "type": "keyword" },
      "is_agency": { "type": "boolean" },
      
      "first_seen": { "type": "date" },
      "last_seen": { "type": "date" },
      "updated_at": { "type": "date" },
      
      "images": { "type": "keyword" },
      "image_count": { "type": "integer" }
    }
  }
}
```

## 3. Sellers Index

```json
// PUT sellers
{
  "mappings": {
    "properties": {
      "seller_id": { "type": "keyword" },
      "phones": { "type": "keyword" },
      "emails": { "type": "keyword" },
      "usernames": { "type": "keyword" },
      "name": { "type": "text" },
      "type": { "type": "keyword" },
      "agency_name": { "type": "text" },
      "confidence": { "type": "float" },
      "detection_signals": { "type": "keyword" },
      
      "total_listings": { "type": "integer" },
      "active_listings": { "type": "integer" },
      "avg_price": { "type": "float" },
      
      "first_seen": { "type": "date" },
      "last_seen": { "type": "date" },
      "properties": { "type": "keyword" }
    }
  }
}
```

## 4. Agents Index (MVP - Simple)

For MVP, just a simple lookup table:

```json
// PUT agents
{
  "mappings": {
    "properties": {
      "phone": { "type": "keyword" },
      "type": { "type": "keyword" },
      "agency_name": { "type": "text" },
      "agency_name_keyword": { "type": "keyword" },
      "source": { "type": "keyword" },
      "scraped_at": { "type": "date" },
      "confidence": { "type": "float" }
    }
  }
}
```
