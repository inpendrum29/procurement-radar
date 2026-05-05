import requests
from supabase import create_client
from datetime import datetime
import hashlib
import os

print("🚀 API CRAWLER START")

SUPABASE_URL = "https://keqavonqytzwxbrygwqc.supabase.co"
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

API_URL = "https://eojn.hr/api/planovi-nabave"

def gen_id(text):
    return hashlib.md5(text.encode()).hexdigest()

def run():
    print("📡 FETCHING EOJN API...")

    resp = requests.get(API_URL)

    if resp.status_code != 200:
        print("❌ API ERROR:", resp.status_code)
        return

    data = resp.json()

    print(f"FOUND RECORDS: {len(data)}")

    for item_raw in data:

        title = item_raw.get("naziv", "N/A")
        authority = item_raw.get("narucitelj", "N/A")

        ext_id = item_raw.get("id") or gen_id(title + authority)

        item = {
            "external_id": str(ext_id),
            "title": title,
            "authority_name": authority,
            "type": "EOJN",
            "estimated_value": 0,
            "year": datetime.now().year,
            "published_at": datetime.now().date().isoformat(),
            "status": "new",
            "source": "EOJN"
        }

        existing = supabase.table("procurement_records") \
            .select("id") \
            .eq("external_id", item["external_id"]) \
            .execute()

        if not existing.data:
            supabase.table("procurement_records").insert(item).execute()
            print("NEW:", title)
        else:
            print("SKIP:", title)

if __name__ == "__main__":
    run()
