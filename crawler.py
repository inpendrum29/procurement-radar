from playwright.sync_api import sync_playwright
from supabase import create_client
from datetime import datetime
import hashlib
import os

print("🚀 EOJN PLAYWRIGHT CRAWLER")

SUPABASE_URL = "https://keqavonqytzwxbrygwqc.supabase.co"
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

URL = "https://eojn.hr/planovi-nabave"

def gen_id(text):
    return hashlib.md5(text.encode()).hexdigest()

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("🌐 OPEN PAGE")
        page.goto(URL, timeout=60000)

        # čekaj da JS render završi
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(8000)

        print("🔍 SEARCHING DATA")

        # EOJN koristi div listu, ne table
        items = page.query_selector_all("div.card")

        print(f"FOUND ITEMS: {len(items)}")

        if len(items) == 0:
            print("❌ NO DATA FOUND - SELECTOR WRONG")
            browser.close()
            return

        for item in items:
            text = item.inner_text()

            ext_id = gen_id(text)

            data = {
                "external_id": ext_id,
                "title": text[:200],
                "authority_name": "EOJN",
                "type": "EOJN",
                "estimated_value": 0,
                "year": datetime.now().year,
                "published_at": datetime.now().date().isoformat(),
                "status": "new",
                "source": "EOJN"
            }

            existing = supabase.table("procurement_records") \
                .select("id") \
                .eq("external_id", data["external_id"]) \
                .execute()

            if not existing.data:
                supabase.table("procurement_records").insert(data).execute()
                print("NEW:", text[:80])
            else:
                print("SKIP")

        browser.close()

if __name__ == "__main__":
    run()
