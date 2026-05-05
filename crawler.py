from playwright.sync_api import sync_playwright
import time

print("🚀 START CRAWLER")

def run():
    print("🌐 OPENING EOJN")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://eojn.hr/planovi-nabave", timeout=60000)

        time.sleep(15)

        print("📄 PAGE LOADED")

        html = page.content()

        print("HTML LENGTH:", len(html))

        if "plan" in html.lower():
            print("✅ PAGE HAS CONTENT")
        else:
            print("❌ EMPTY PAGE")

        browser.close()

if __name__ == "__main__":
    run()
