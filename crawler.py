crawler.py
from playwright.sync_api import sync_playwright
from supabase import create_client
from datetime import datetime
import hashlib
import os

SUPABASE_URL = "https://keqavonqytzwxbrygwqc.supabase.co"
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

URL = "https://eojn.hr/planovi-nabave"

def clean(t):
    return t.strip() if t else ""

def gen_id(text):
    return hashlib.md5(text.encode()).hexdigest()

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL)
        page.wait_for_timeout(3000)

        rows = page.query_selector_all("table tr")

        for r in rows[1:]:
            cols = r.query_selector_all("td")
            if len(cols) < 3:
                continue

            title = clean(cols[1].inner_text())
            authority = clean(cols[2].inner_text())

            ext_id = clean(cols[0].inner_text()) or gen_id(title)

            item = {
                "external_id": ext_id,
                "title": title,
                "authority_name": authority,
                "type": "EOJN",
                "year": datetime.now().year,
                "published_at": datetime.now().date().isoformat(),
                "status": "new"
            }

            existing = supabase.table("procurement_records") \
                .select("id") \
                .eq("external_id", item["external_id"]) \
                .execute()

            if not existing.data:
                supabase.table("procurement_records").insert(item).execute()
                print("NEW:", title)

        browser.close()

if __name__ == "__main__":
    run()
