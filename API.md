# Smart Real Estate Search API - Documentation

## Overview

Natural language search API for Romanian real estate powered by LLM query parsing and OpenSearch hybrid search.

### Architecture

```
┌─────────────────┐
│   User Query    │  "apartament 2 camere in Pallady, pet friendly"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │  ← JWT Auth (Keycloak)
│   /search       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   LLM Parser    │  Ollama (gpt-oss:20b-cloud)
│   (~2-3 sec)    │  → Extracts: location, rooms, price, features
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Query Builder  │  Builds OpenSearch DSL query:
│                 │  - must: rooms=2, transaction_type=Inchiriere
│                 │  - should: location fuzzy match, neural search
│                 │  - must_not: "fara animale" if pet_friendly
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   OpenSearch    │  Hybrid search (BM25 + BGE-M3 embeddings)
│   (~50ms)       │  Returns top 20 results
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Response     │  Streamlined JSON for card UI
└─────────────────┘
```

**Key Point**: The LLM only parses the query into structured filters. It never sees results. This ensures deterministic, reproducible searches with no hallucinated results.

---

## Endpoints

### POST /search

Natural language search for real estate listings.

**Request:**
```json
{
  "query": "apartament 2 camere de inchiriat in Pallady, pet friendly, sub 600 euro",
  "session_id": "optional-uuid"  // omit for new session
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "query": "apartament 2 camere de inchiriat in Pallady, pet friendly, sub 600 euro",
  "total_results": 15,
  "filters_applied": {
    "location": "Pallady",
    "transaction_type": "Inchiriere",
    "rooms": 2,
    "max_price": 600,
    "currency": "EUR",
    "pet_friendly": true
  },
  "results": [
    {
      "id": "296515647",
      "ad_id": "296515647",
      "title": "Apartament 2 camere Pallady - pet friendly",
      "description": "Apartament modern, complet mobilat...",
      "price": 550.0,
      "currency": "EUR",
      "location": "Bucuresti, Sectorul 3",
      "categories": ["Inchiriere", "Apartamente", "2 camere"],
      "surface": "54 m²",
      "phone": "0722123456",
      "date": "12/03/25, 10:13 AM",
      "images": ["https://...", "https://..."],
      "image_count": 7,
      "source": "olx",
      "url": "https://www.olx.ro/..."
    }
  ]
}
```

### GET /session/{session_id}

Get current session state (active filters, conversation context).

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user": "vladxpetrescu@gmail.com",
  "filters": {
    "location": "Pallady",
    "rooms": 2,
    "max_price": 600
  },
  "created_at": "2025-12-05T22:30:00Z",
  "last_query": "sub 600 euro"
}
```

### GET /session/{session_id}/history

Get conversation history for a session.

### DELETE /session/{session_id}

Delete a session and its history.

### POST /session/{session_id}/reset

Reset session filters while keeping the session alive.

### GET /sessions

List all sessions for the authenticated user.

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-12-05T22:30:00Z",
      "last_query": "apartament pallady"
    }
  ]
}
```

### GET /me

Get current authenticated user info.

**Response:**
```json
{
  "username": "vladxpetrescu@gmail.com",
  "email": "vladxpetrescu@gmail.com",
  "roles": ["user"]
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "opensearch": "connected",
  "llm": "connected"
}
```

---

## Authentication

The API uses Keycloak JWT tokens for authentication.

### Getting a Token

```bash
# Get token from Keycloak
TOKEN=$(curl -s -X POST \
  'https://auth.immocloud.ro/realms/immocloud/protocol/openid-connect/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=password' \
  -d 'client_id=immo-search' \
  -d 'client_secret=kiytWUd0qXBHizJkRdRD6Fv8AZ5L3mmo' \
  -d 'username=YOUR_USERNAME' \
  -d 'password=YOUR_PASSWORD' | jq -r '.access_token')
```

### Using the Token

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "apartament 2 camere pallady"}'
```

### Document Level Security (DLS)

Each user can only see their own sessions. Sessions are stored in OpenSearch with the user's `preferred_username` as ownership identifier.

---

## Natural Language Features

### Supported Query Types

| Query | Extracted Filters |
|-------|------------------|
| "apartament 2 camere" | rooms=2, property_type=apartament |
| "garsoniera de inchiriat" | rooms=1, transaction_type=inchiriere |
| "casa in Pipera sub 300000 euro" | location=Pipera, max_price=300000, currency=EUR |
| "pet friendly" | pet_friendly=true (excludes "fara animale") |
| "etaj 3" | floor=3 |
| "cu parcare" | has_parking=true |
| "sectorul 6" / "sector 6" / "s6" | location=Sectorul 6 |

### Conversation Memory

Follow-up queries build on previous context:

```
Query 1: "apartament 2 camere in Pallady"
→ Filters: {rooms: 2, location: "Pallady"}

Query 2: "sub 600 euro"
→ Filters: {rooms: 2, location: "Pallady", max_price: 600}

Query 3: "pet friendly"
→ Filters: {rooms: 2, location: "Pallady", max_price: 600, pet_friendly: true}
```

### Location Fuzzy Matching

The search uses fuzzy matching for Bucharest neighborhoods:
- "Pallady", "palladi", "paladi" → matches "Nicolae Grigorescu, Pallady"
- "s6", "sector 6", "sectorul 6" → matches "Sectorul 6"
- "Militari" → matches "Militari, Lujerului, Gorjului"

---

## Deployment

### Docker

```bash
# Build and run
docker-compose -f docker-compose.api.yml up -d

# Check logs
docker logs -f smart-search-api

# Stop
docker-compose -f docker-compose.api.yml down
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_ENABLED` | true | Enable JWT authentication |
| `KEYCLOAK_URL` | https://auth.immocloud.ro | Keycloak server URL |
| `KEYCLOAK_REALM` | immocloud | Keycloak realm |
| `KEYCLOAK_CLIENT_ID` | immo-search | OAuth client ID |
| `KEYCLOAK_CLIENT_SECRET` | - | OAuth client secret |
| `OPENSEARCH_HOST` | 192.168.40.101 | OpenSearch host |
| `OPENSEARCH_PORT` | 9200 | OpenSearch port |
| `OPENSEARCH_USER` | admin | OpenSearch username |
| `OPENSEARCH_PASSWORD` | - | OpenSearch password |
| `LLM_BASE_URL` | http://192.168.10.115:11434 | Ollama API URL |
| `LLM_MODEL` | gpt-oss:20b-cloud | LLM model for parsing |
| `EMBEDDING_MODEL_ID` | RP2W5ZoB-XLRYbYP-LKJ | BGE-M3 model ID in OpenSearch |

### Production Configuration

For production, set these in `docker-compose.api.yml`:

```yaml
services:
  search-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 256M
      replicas: 3  # Scale horizontally
```

---

## Performance

### Request Latency Breakdown

| Component | Time | Notes |
|-----------|------|-------|
| JWT Validation | ~5ms | JWKS cached for 5 min |
| LLM Parsing | 2-3 sec | **Bottleneck** - depends on LLM hardware |
| OpenSearch Query | ~50ms | Hybrid search with aggregations |
| Response Formatting | ~5ms | Python processing |
| **Total** | **~2.5-3.5 sec** | First query in session |

Follow-up queries in the same session can be faster if context is reused.

### Estimated Throughput

With the current setup (single Ollama instance):

| Scenario | Requests/sec | Notes |
|----------|-------------|-------|
| **Sequential** | ~0.3-0.4 rps | Limited by LLM |
| **Concurrent (2 workers)** | ~0.6-0.8 rps | Ollama can batch |
| **With LLM caching** | ~1-2 rps | If identical queries |

### Scaling Recommendations

1. **LLM Bottleneck**: The LLM is the slowest component
   - Use faster hardware (GPU)
   - Deploy multiple Ollama instances behind a load balancer
   - Consider smaller/faster models (7B instead of 20B)

2. **Horizontal Scaling**: Run multiple API instances
   ```yaml
   deploy:
     replicas: 3
   ```
   Each instance handles requests independently.

3. **Caching**: Add Redis cache for:
   - Parsed query results (same query → same filters)
   - Common search patterns

4. **OpenSearch**: Already fast, but can optimize with:
   - More shards for larger indices
   - Dedicated ML nodes for embedding inference

### Monitoring

The `/health` endpoint returns:
```json
{
  "status": "healthy",
  "opensearch": "connected",
  "llm": "connected"
}
```

For production, integrate with:
- Prometheus metrics
- Grafana dashboards
- Log aggregation (ELK/Loki)

---

## Development

### Running Locally

```bash
# Activate virtualenv
cd /home/vlad/repos/frontend-llm
source venv/bin/activate

# Set environment
export AUTH_ENABLED=false  # Disable auth for testing

# Run with auto-reload
uvicorn api.main:app --reload --port 8000
```

### API Documentation

FastAPI auto-generates interactive docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Testing

```bash
# Health check
curl http://localhost:8000/health

# Search (without auth)
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "apartament 2 camere pallady"}'
```

---

## Error Handling

| Status | Description |
|--------|-------------|
| 200 | Success |
| 400 | Bad request (invalid query) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (no access to resource) |
| 404 | Session not found |
| 500 | Server error |
| 503 | LLM or OpenSearch unavailable |

Error response format:
```json
{
  "detail": "Error message describing the issue"
}
```
