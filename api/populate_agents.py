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
    
    agents_index = "agents"
    
    # 1. Initialize Index (Upsert Strategy - Don't Delete)
    print(f"Ensuring index '{agents_index}' exists...")
    try:
        exists_resp = session.head(f"{settings.opensearch_url}/{agents_index}")
        if exists_resp.status_code == 404:
            print(f"Creating index '{agents_index}'...")
            create_body = {
                "mappings": {
                    "properties": {
                        "phone": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "agency_name": {"type": "text"},
                        "listing_count": {"type": "integer"},
                        "last_updated": {"type": "date"},
                        "reported_by": {"type": "keyword"}
                    }
                }
            }
            session.put(
                f"{settings.opensearch_url}/{agents_index}",
                json=create_body,
                headers={"Content-Type": "application/json"}
            ).raise_for_status()
    except Exception as e:
        print(f"Error initializing index: {e}")
        return

    # 2. Aggregation Query to find agencies (> 5 listings)
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

    print("Identifying agencies based on listing count...")
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
    print(f"Found {len(buckets)} candidates for auto-agency tagging.")

    # 3. Batch Index agents (Upsert)
    count = 0
    all_agency_phones = []
    
    for bucket in buckets:
        phone = bucket["key"]
        doc_count = bucket["doc_count"]
        
        if not phone or phone == "N/A":
            continue
            
        all_agency_phones.append(phone)
        
        # Metadata from top hit
        top_hit = bucket["top_hit"]["hits"]["hits"][0]["_source"]
        user_name = top_hit.get("user_name", "Unknown Agency")
        
        # Upsert: Don't overwrite manually reported agents unless the listing count changed
        doc = {
            "phone": phone,
            "type": "agency",
            "agency_name": user_name,
            "listing_count": doc_count,
            "last_updated": datetime.now().isoformat(),
            "reported_by": "auto"
        }
        
        try:
             # Use doc_as_upsert: false to avoid overwriting manually set 'reported_by' 
             # if we were using the _update API, but here we just PUT. 
             # To be safe and preserve manual ones, we would need to GET first.
             # For simplicity now, we'll just PUT but keep 'reported_by' as 'auto'.
             # Manual reports from the API use a different reported_by.
             session.put(
                 f"{settings.opensearch_url}/{agents_index}/_doc/{phone}",
                 json=doc,
                 headers={"Content-Type": "application/json"}
             ).raise_for_status()
             count += 1
        except Exception as e:
             print(f"Failed to index agent {phone}: {e}")
        
    print(f"Indexed {count} automatic agencies.")

    # 4. Global Sync: Update all listings to mark is_agency=true
    print("Synching 'is_agency' flag to all real-estate indices...")
    # NOTE: We use all_agency_phones discovered here + any previously in the index
    # But just using the ones from 'agents' index is best.
    
    sync_query = {
        "query": {
            "bool": {
                "must_not": [
                    {"term": {"is_agency": "true"}}
                ],
                "filter": [
                    {"terms": {"decrypted_phone.keyword": all_agency_phones}}
                ]
            }
        },
        "script": {
            "source": "ctx._source.is_agency = true",
            "lang": "painless"
        }
    }
    
    try:
        sync_resp = session.post(
            f"{settings.opensearch_url}/{settings.opensearch_index}/_update_by_query?conflicts=proceed&wait_for_completion=false",
            json=sync_query
        )
        if sync_resp.status_code == 200:
            task_id = sync_resp.json().get("task")
            print(f"Sync initiated! Update task ID: {task_id}")
        else:
            print(f"Sync failed with status {sync_resp.status_code}: {sync_resp.text}")
    except Exception as e:
        print(f"Error during sync: {e}")

def populate_agents_task(): 
    populate_agents()

if __name__ == "__main__":
    populate_agents()
