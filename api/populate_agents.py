import os
import sys
import json
import requests
import warnings
from datetime import datetime

# Add current directory to path to import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import settings
except ImportError:
    # Fallback if run from different location
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    from config import settings

# Suppress SSL warnings
warnings.filterwarnings("ignore")

def populate_agents():
    print(f"Connecting to OpenSearch at {settings.opensearch_url} via requests...")
    
    session = requests.Session()
    session.auth = settings.opensearch_auth
    session.verify = settings.opensearch_verify_ssl
    
    # 1. Aggregation Query
    query = {
        "size": 0,
        "aggs": {
            "phones": {
                "terms": {
                    "field": "decrypted_phone.keyword",
                    "size": 10000,
                    "min_doc_count": 5
                },
                "aggs": {
                    "top_hit": {
                        "top_hits": {
                            "size": 1,
                            "_source": ["user_name", "ad_source"]
                        }
                    }
                }
            }
        }
    }

    print("Running aggregation query to identify agencies (listings > 5)...")
    try:
        resp = session.post(
            f"{settings.opensearch_url}/{settings.opensearch_index}/_search",
            json=query,
            headers={"Content-Type": "application/json"}
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Error querying index {settings.opensearch_index}: {e}")
        return

    buckets = data.get("aggregations", {}).get("phones", {}).get("buckets", [])
    print(f"Found {len(buckets)} potential agencies.")

    agents_index = "agents"
    
    # 2. Reset agents index (Delete and Recreate) to ensure fresh data
    print(f"Resetting index '{agents_index}'...")
    try:
        # Delete index if exists
        del_resp = session.delete(f"{settings.opensearch_url}/{agents_index}")
        if del_resp.status_code == 200:
            print(f"Deleted existing index '{agents_index}'.")
        elif del_resp.status_code == 404:
            print(f"Index '{agents_index}' did not exist.")
        else:
             print(f"Warning: Failed to delete index (Status {del_resp.status_code})")

        # Create index
        print(f"Creating index '{agents_index}'...")
        create_body = {
            "mappings": {
                "properties": {
                    "phone": {"type": "keyword"},
                    "type": {"type": "keyword"},
                    "agency_name": {"type": "text"},
                    "listing_count": {"type": "integer"},
                    "last_updated": {"type": "date"}
                }
            }
        }
        session.put(
            f"{settings.opensearch_url}/{agents_index}",
            json=create_body,
            headers={"Content-Type": "application/json"}
        ).raise_for_status()
        
    except Exception as e:
        print(f"Error resetting index: {e}")
        return

    # 3. Index agents
    count = 0
    for bucket in buckets:
        phone = bucket["key"]
        doc_count = bucket["doc_count"]
        
        if not phone or phone == "N/A":
            continue
            
        # Extract metadata from top hit
        top_hit = bucket["top_hit"]["hits"]["hits"][0]["_source"]
        user_name = top_hit.get("user_name", "Unknown")
        if not user_name: 
            user_name = "Unknown Agency"
            
        # Prepare document
        doc = {
            "phone": phone,
            "type": "agency",
            "agency_name": user_name,
            "listing_count": doc_count,
            "last_updated": datetime.now().isoformat()
        }
        
        # Index (upsert via PUT /index/_doc/id)
        try:
             # Using phone number as ID for easy deduplication/updating
             session.put(
                 f"{settings.opensearch_url}/{agents_index}/_doc/{phone}",
                 json=doc,
                 headers={"Content-Type": "application/json"}
             ).raise_for_status()
             count += 1
        except Exception as e:
             print(f"Failed to index agent {phone}: {e}")
        
    print(f"Successfully indexed {count} agencies into '{agents_index}'.")

def populate_agents_task(): 
    populate_agents()

if __name__ == "__main__":
    populate_agents()
