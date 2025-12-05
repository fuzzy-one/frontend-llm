# Future Architecture - Data Platform

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SCRAPING PIPELINE                            │
│                     (runs continuously/daily)                       │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      RAW ADS INDEX                                  │
│                   real-estate-raw-*                                 │
│                                                                     │
│  Every scrape = new document (versioned)                            │
│  {                                                                  │
│    "ad_id": "olx-123",                                              │
│    "source": "olx",                                                 │
│    "scraped_at": "2025-12-05T10:00:00Z",                           │
│    "version": 3,           ← increments each re-scrape             │
│    "price": 95000,                                                  │
│    "hash": "abc123...",    ← content hash for change detection     │
│    ...all raw data...                                               │
│  }                                                                  │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │     PROCESSING JOBS       │
                    │    (async, scheduled)     │
                    └─────────────┬─────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────────┐
│ DEDUP JOB     │       │ AGENT DETECT  │       │ PRICE HISTORY JOB │
│               │       │               │       │                   │
│ - Image hash  │       │ - Phone freq  │       │ - Track changes   │
│ - Text simil. │       │ - Keywords    │       │ - Store deltas    │
│ - Address     │       │ - Blacklist   │       │ - Trend analysis  │
│ - Coords      │       │               │       │                   │
└───────┬───────┘       └───────┬───────┘       └─────────┬─────────┘
        │                       │                         │
        └───────────────────────┴─────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CANONICAL PROPERTIES INDEX                       │
│                        properties-*                                 │
│                                                                     │
│  One doc per ACTUAL property (deduplicated)                         │
│  {                                                                  │
│    "property_id": "prop-uuid-123",                                  │
│    "canonical_title": "Apartament 2 camere Titan",                 │
│    "current_price": 95000,                                          │
│    "listings": [                   ← all sources merged             │
│      {"source": "olx", "ad_id": "olx-123", "url": "..."},          │
│      {"source": "imobiliare", "ad_id": "imob-456", "url": "..."},  │
│    ],                                                               │
│    "price_history": [              ← trend tracking                 │
│      {"date": "2025-10-01", "price": 100000},                      │
│      {"date": "2025-11-15", "price": 98000},                       │
│      {"date": "2025-12-05", "price": 95000},                       │
│    ],                                                               │
│    "is_agency": false,                                              │
│    "seller_type": "private",       ← private/agent/agency          │
│    "seller_id": "seller-789",      ← links to sellers index        │
│    "first_seen": "2025-10-01",                                     │
│    "last_seen": "2025-12-05",                                      │
│    "status": "active",             ← active/sold/expired           │
│  }                                                                  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        SELLERS INDEX                                │
│                          sellers                                    │
│                                                                     │
│  {                                                                  │
│    "seller_id": "seller-789",                                       │
│    "phones": ["0722123456", "0733123456"],                         │
│    "type": "agent",                ← private/agent/agency          │
│    "agency_name": "Imobiliare XYZ",                                │
│    "confidence": 0.95,                                              │
│    "total_listings": 47,                                            │
│    "active_listings": 12,                                           │
│    "avg_price": 125000,                                             │
│    "properties": ["prop-123", "prop-456", ...],                    │
│  }                                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Current MVP vs Future State

### MVP (Now)
- `real-estate-*` - all ads (as-is)
- `agents` - known agent phones (cross-index lookup)
- Simple flag on search results

### Future State
- `real-estate-raw-*` - versioned raw scrapes
- `properties` - deduplicated canonical properties
- `sellers` - enriched seller profiles
- Full price history & trend tracking
