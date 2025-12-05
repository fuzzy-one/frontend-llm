# Price History & Trend Tracking

## Goal

Track price changes over time to:
1. Show price drop alerts 🔥
2. Display price history charts 📊
3. Identify negotiable sellers
4. Detect market trends

## Data Model

```json
{
  "property_id": "prop-123",
  "current_price": 95000,
  "currency": "EUR",
  "price_history": [
    {"date": "2025-10-01", "price": 100000, "source": "olx"},
    {"date": "2025-11-15", "price": 98000, "source": "olx"},
    {"date": "2025-12-05", "price": 95000, "source": "imobiliare"}
  ],
  "price_trend": "down",
  "price_drop_pct": 5.0,
  "days_on_market": 65
}
```

## Re-scraping Strategy

- Scrape every 2-3 days
- Compare new price with last known price
- If changed: add to `price_history[]`
- Calculate trend: up/down/stable

## Implementation (Future)

```python
def track_price_changes(os_client, new_ad: dict, property_id: str):
    """Track price change for a property"""
    
    property_doc = os_client.get(index='properties', id=property_id)['_source']
    
    old_price = property_doc.get('current_price')
    new_price = new_ad.get('price')
    
    if old_price and new_price and old_price != new_price:
        history_entry = {
            'date': new_ad['scraped_at'],
            'price': new_price,
            'source': new_ad['source'],
            'change_pct': ((new_price - old_price) / old_price) * 100
        }
        
        update = {
            "script": {
                "source": """
                    ctx._source.price_history.add(params.entry);
                    ctx._source.current_price = params.new_price;
                    ctx._source.price_trend = params.trend;
                    if (params.drop_pct > 0) {
                        ctx._source.price_drop_pct = params.drop_pct;
                    }
                """,
                "params": {
                    "entry": history_entry,
                    "new_price": new_price,
                    "trend": "down" if new_price < old_price else "up",
                    "drop_pct": max(0, ((old_price - new_price) / old_price) * 100)
                }
            }
        }
        
        os_client.update(index='properties', id=property_id, body=update)
        
        # Alert if significant drop
        if history_entry['change_pct'] < -5:
            print(f"🔥 Price drop: {property_id} dropped {abs(history_entry['change_pct']):.1f}%")
```

## UI Features

| Feature | Data Source |
|---------|-------------|
| 📉 "Price dropped 5%!" badge | `price_drop_pct > 5` |
| 📊 Price history sparkline | `price_history[]` |
| ⏰ "65 days on market" | `days_on_market` |
| 🔥 Hot deal indicator | `price_trend == "down"` |

## Rental Property Tracking

For rentals, track yearly re-listings:
- Same address + same landlord phone
- Compare year-over-year rent changes
- "This unit was €450 last year, now €500"
