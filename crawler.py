import os
import hashlib
from datetime import datetime

import requests
from supabase import create_client

print("🚀 EOJN API CRAWLER STARTED")

SUPABASE_URL = "https://keqavonqytzwxbrygwqc.supabase.co"
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# TEST endpoint approach — ako EOJN endpoint ne vrati podatke, barem ćemo to jasno vidjeti u logu
EOJN_PAGE_URL = "https://eojn.hr/planovi-nabave"
EOJN_API_URL = "https://eojn.hr/planovi-nabave/api/search"


def gen_id(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def normalize_record(raw: dict) -> dict:
    title = (
        raw.get("naziv")
        or raw.get("title")
        or raw.get("nazivPredmeta")
        or raw.get("predmet")
        or "N/A"
    )

    authority = (
        raw.get("naruciteljNaziv")
        or raw.get("narucitelj")
        or raw.get("authority")
        or raw.get("nazivNarucitelja")
        or "N/A"
    )

    external_id = (
        raw.get("id")
        or raw.get("external_id")
        or raw.get("evidencijskiBroj")
        or gen_id(title + authority)
    )

    return {
        "external_id": str(external_id),
        "title": str(title),
        "authority_name": str(authority),
        "type": "EOJN",
        "estimated_value": 0,
        "year": datetime.now().year,
        "published_at": datetime.now().date().isoformat(),
        "status": "new",
        "source": "EOJN",
    }


def extract_items(data):
    """
    Pokušava podržati više mogućih JSON formata:
    - lista zapisa
    - {"content": [...]}
    - {"items": [...]}
    - {"data": [...]}
    - {"results": [...]}
    """
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ["content", "items", "data", "results", "records"]:
            if key in data and isinstance(data[key], list):
                return data[key]

    return []


def save_item(item: dict) -> None:
    existing = (
        supabase.table("procurement_records")
        .select("id")
        .eq("external_id", item["external_id"])
        .execute()
    )

    if existing.data:
        print("SKIP:", item["title"])
        return

    supabase.table("procurement_records").insert(item).execute()
    print("NEW:", item["title"])


def run():
    print("📡 LOADING EOJN PAGE")

    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Referer": EOJN_PAGE_URL,
    }

    # 1) Otvori stranicu radi session/cookie konteksta
    page_response = session.get(EOJN_PAGE_URL, headers=headers, timeout=30)
    print("PAGE STATUS:", page_response.status_code)

    # 2) Pokušaj API search endpoint
    payloads = [
        {"page": 1, "size": 50},
        {"pageNumber": 0, "pageSize": 50},
        {"page": 0, "limit": 50},
        {},
    ]

    for idx, payload in enumerate(payloads, start=1):
        print(f"📡 TRY API PAYLOAD #{idx}:", payload)

        response = session.post(
            EOJN_API_URL,
            json=payload,
            headers=headers,
            timeout=30,
        )

        print("API STATUS:", response.status_code)
        print("API CONTENT-TYPE:", response.headers.get("content-type", ""))

        if response.status_code != 200:
            print("API TEXT PREVIEW:", response.text[:300])
            continue

        try:
            data = response.json()
        except Exception:
            print("❌ RESPONSE IS NOT JSON")
            print("TEXT PREVIEW:", response.text[:500])
            continue

        items = extract_items(data)
        print("FOUND RECORDS:", len(items))

        if not items:
            print("JSON PREVIEW:", str(data)[:500])
            continue

        for raw in items:
            item = normalize_record(raw)
            save_item(item)

        print("✅ DONE")
        return

    print("❌ NO WORKING EOJN API PAYLOAD FOUND")
    print("Ako vidiš ovo, endpoint nije točan ili EOJN koristi drugi API poziv.")


if __name__ == "__main__":
    run()
