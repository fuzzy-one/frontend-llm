# OpenSearch Configuration & Changes

## Overview
This document outlines the current state of OpenSearch indices, mappings, and the logic used for identifying real estate agencies.

## 1. Agency Identification (`agents` Index)

### Purpose
Stores identified real estate agencies and agents to allow filtering/exclusion in search results.

### Source of Truth
- **Population Script**: `api/populate_agents.py`
- **Logic**: Aggregates `real-estate-*` indices by `decrypted_phone`. Any phone number associated with **>5 listings** is classified as an agency.

### Index Mapping (`agents`)
| Field | Type | Description |
|-------|------|-------------|
| `phone` | keyword | Primary key (decrypted phone number). |
| `type` | keyword | Seller type (e.g., `agency`, `agent`). |
| `agency_name` | text/keyword | Name of the agency (if available). |
| `ad_count` | integer | Number of listings detected for this phone. |
| `last_updated` | date | Timestamp of the last update. |
| `confidence` | float | System confidence in this classification (default 1.0). |

## 2. Real Estate Listings (`real-estate-*`)

### Purpose
Stores the actual property listings scraped from various sources (OLX, Romimo, Anuntul).

### Index Pattern
- `real-estate-{YYYY.MM.dd}` (Daily indices managed by Logstash)

### Key Fields (relevant to search)
- `decypted_phone`: The phone number used for cross-referencing with the `agents` index.
- `location_1`, `location_2`, `location_3`: Hierarchical location data.
- `price`, `currency`: Pricing information.
- `description`, `title`: searchable text fields.

## 3. Agency Exclusion Logic

### Current Implementation ("Post-Processing")
1.  **Search**: API queries `real-estate-*` for `N` results.
2.  **Enrich**: API extracts phone numbers from results and queries the `agents` index.
3.  **Filter**: If `exclude_agencies=True`, the API filters out matches *in memory* before returning the response.
    - *Note*: This causes pagination "jitter" (e.g., requesting 25 items might return only 15 if 10 were agencies).

### Planned Implementation ("Denormalization")
To fix pagination jitter, we are moving to a denormalized model:
1.  **Sync Job**: A periodic script will tag `real-estate-*` documents with `is_agency: true` based on the `agents` index.
2.  **Ingest Tagging**: Logstash will be configured to tag incoming listings in real-time.
3.  **Native Filtering**: Search queries will use `must_not: { term: { is_agency: true } }` for zero-jitter performance.

> **Note on Ingest Pipelines**: The OpenSearch `enrich` processor is **not available** in the current installed version, so we are using Logstash for ingest-time enrichment instead.
