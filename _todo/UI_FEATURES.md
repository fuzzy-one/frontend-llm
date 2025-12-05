# Future UI Features

## Enabled by Data Platform

| Feature | Data Source | Priority |
|---------|-------------|----------|
| 🏷️ "Private seller" badge | `is_agency: false` | MVP |
| 🏢 "Agency" badge | `is_agency: true` | MVP |
| 📉 Price drop indicator | `price_trend: "down"` | Phase 2 |
| 📊 Price history chart | `price_history[]` | Phase 2 |
| 🔗 "View on 3 sites" button | `listings[]` | Phase 2 |
| ⏰ "Listed 2 months ago" | `first_seen` | Phase 2 |
| 👤 "This seller has 12 listings" | `sellers` index | Phase 2 |
| 🔥 "Price dropped 10%!" alert | `price_drop_pct > 5` | Phase 2 |
| 📍 Similar properties nearby | geo_distance query | Phase 3 |
| 💰 Price per sqm comparison | computed field | Phase 3 |

## MVP Response

```json
{
  "id": "123",
  "title": "Apartament 2 camere Titan",
  "price": 95000,
  "is_agency": false,
  "seller_type": "private",
  "score": 87
}
```

## Phase 2 Response

```json
{
  "property_id": "prop-uuid-123",
  "title": "Apartament 2 camere Titan",
  "price": 95000,
  "currency": "EUR",
  "price_trend": "down",
  "price_drop_pct": 5.3,
  "price_history": [
    {"date": "2025-10-01", "price": 100000},
    {"date": "2025-12-05", "price": 95000}
  ],
  "seller_type": "private",
  "is_agency": false,
  "listings": [
    {"source": "olx", "url": "https://olx.ro/..."},
    {"source": "imobiliare.ro", "url": "https://imobiliare.ro/..."}
  ],
  "listing_count": 2,
  "first_seen": "2025-10-01",
  "days_on_market": 65,
  "score": 87
}
```

## CSS for Score Bullet

```css
.score-bullet {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.score-high { background: #22c55e; }    /* 80-100 */
.score-medium { background: #eab308; }  /* 60-79 */
.score-low { background: #f97316; }     /* 40-59 */
.score-poor { background: #ef4444; }    /* 0-39 */
```

## CSS for Price Trend

```css
.price-trend-down {
  color: #22c55e;  /* green - good for buyer */
}
.price-trend-down::before {
  content: "↓ ";
}

.price-trend-up {
  color: #ef4444;  /* red - bad for buyer */
}
.price-trend-up::before {
  content: "↑ ";
}
```

## Seller Badge

```css
.seller-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.seller-private {
  background: #dcfce7;
  color: #166534;
}
.seller-agent {
  background: #fef3c7;
  color: #92400e;
}
.seller-agency {
  background: #fee2e2;
  color: #991b1b;
}
```
