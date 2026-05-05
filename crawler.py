import requests
from supabase import create_client
from datetime import datetime
import hashlib
import os

print("🚀 EOJN API CRAWLER")

SUPABASE_URL = "https://keqavonqytzwxbrygwqc.supabase.co"
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

URL = "https://eojn.hr/planovi-nabave"

def gen_id(text):
    return hashlib.md5(text.encode()).hexdigest()

def run():
    print("📡 LOADING PAGE")

    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    # prvo otvorimo stranicu (cookie/session)
    session.get(URL, headers=headers)

    # pravi endpoint koji EOJN koristi (search API)
    api_url = "https://eojn.hr/planovi-nabave/api/search"

    payload = {
        "page": 1,
        "size": 50
    }

    resp = session.post(api_url, json=payload, headers=headers)

    if resp.status_code != 200:
        print("❌ API ERROR:", resp.status_code)
        print(resp.text)
        return

    data = resp.json()

    items = data.get("content", [])

    print(f"FOUND RECORDS: {len(items)}")

    for item_raw in items:
        title = item_raw.get("naziv", "N/A")
        authority = item_raw.get("naruciteljNaziv", "N/A")

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
