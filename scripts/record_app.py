"""Record genuine browser interaction with the running Streamlit app."""
import json
import time
from pathlib import Path
import shutil

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "media" / "demo" / "raw"
ASSETS = ROOT / "media" / "demo" / "assets"
RAW.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            record_video_dir=str(RAW),
            record_video_size={"width": 1920, "height": 1080},
            color_scheme="dark",
        )
        page = context.new_page()
        page.goto("http://127.0.0.1:8501", wait_until="networkidle", timeout=30000)
        button = page.get_by_role("button", name="Research with live sources")
        button.wait_for(state="visible")
        if not button.is_enabled():
            raise RuntimeError("The live research button is disabled; check .env and restart the app")
        field = page.get_by_label("Research question")
        field.fill("")
        field.press_sequentially("What does recent evidence say about the benefits and limitations of heat pumps in cold climates?", delay=35)
        page.screenshot(path=str(ASSETS / "01_question.png"))
        time.sleep(8)
        button.click()
        page.get_by_text("Research report", exact=True).wait_for(timeout=180000)
        page.get_by_text("Research report", exact=True).scroll_into_view_if_needed()
        page.screenshot(path=str(ASSETS / "02_report.png"))
        time.sleep(10)
        page.get_by_text("Original sources", exact=True).scroll_into_view_if_needed()
        page.screenshot(path=str(ASSETS / "03_sources.png"))
        time.sleep(8)
        source_expanders = page.locator("div[data-testid='stExpander']")
        if source_expanders.count():
            source_expanders.first.click()
            time.sleep(4)
            page.screenshot(path=str(ASSETS / "04_source_detail.png"))
            time.sleep(6)
            source_link = page.get_by_role("link", name="Open original source").first
            source_url = source_link.get_attribute("href")
            if source_url and source_url.startswith(("https://", "http://")):
                source_page = context.new_page()
                source_page.goto(source_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(4)
                source_page.screenshot(path=str(ASSETS / "06_original_page.png"))
                print("Opened original source:", source_page.url)
                source_page.close()
        trace = page.get_by_text("Reproducible research trace", exact=True)
        trace.scroll_into_view_if_needed()
        trace.click()
        time.sleep(5)
        page.screenshot(path=str(ASSETS / "05_trace.png"))
        time.sleep(5)
        video = page.video
        context.close()
        browser.close()
        destination = RAW / "app_run.webm"
        shutil.move(video.path(), destination)
        print("Recorded actual app interaction:", destination)
        print("Screenshots:", len(list(ASSETS.glob("0*.png"))))


if __name__ == "__main__":
    main()
