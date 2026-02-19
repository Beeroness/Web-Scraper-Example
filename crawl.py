#!/usr/bin/env python3
"""
crawl.py — NASA Open Data Portal (CKAN) Web Scraper

Scrapes datasets from data.nasa.gov for a given tag and
writes structured records to a JSONL file.

Usage:
    python crawl.py --tag cassini --out datasets.jsonl
"""

import argparse
import json
import time
import requests
from bs4 import BeautifulSoup

# ─── CONFIGURATION ───────────────────────────────────────────────
BASE_URL = "https://data.nasa.gov"
LISTING_URL = f"{BASE_URL}/dataset/"
DELAY = 1  # seconds between requests (be polite!)

# Track pages we've already visited so we never hit the same one twice
seen_urls = set()


def fetch_page(url):
    """
    Fetch a URL and return a BeautifulSoup object.
    - Skips URLs we've already visited
    - Waits 1 second between requests (rate limiting)
    - Returns None if anything goes wrong
    """
    if url in seen_urls:
        print(f"  [SKIP] Already visited: {url}")
        return None

    seen_urls.add(url)
    print(f"  [FETCH] {url}")

    try:
        time.sleep(DELAY)  # rate limit: 1 request per second
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"  [ERROR] Failed to fetch {url}: {e}")
        return None


def get_dataset_links(tag, page_num):
    """
    Given a tag and page number, fetch the listing page and
    return a list of full dataset detail-page URLs.
    """
    url = f"{LISTING_URL}?tags={tag}&page={page_num}"
    soup = fetch_page(url)
    if soup is None:
        return []

    links = []
    # Each dataset title on the listing page is a link inside an <h3> 
    # within the dataset-list. We grab all <a> tags whose href starts
    # with /dataset/ (but skip the main /dataset/ page itself).
    for a_tag in soup.select("h2.dataset-heading a"):
        href = a_tag.get("href", "")
        if href and href.startswith("/dataset/") and href != "/dataset/" and "?" not in href:
            full_url = BASE_URL + href
            links.append(full_url)

    return links


def scrape_dataset(url):
    """
    Visit a single dataset detail page and extract all required fields.
    Returns a dictionary with the dataset record, or None on failure.
    """
    soup = fetch_page(url)
    if soup is None:
        return None

    text_sources = [url]  # track which pages we scraped text from

    # ── TITLE ──
    # We confirmed this is in an <h1> tag
    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else "Unknown Title"

    # ── DESCRIPTION ──
    # We confirmed this is in <div class="notes embedded-content">
    notes_div = soup.find("div", class_="notes")
    if notes_div:
        description = notes_div.get_text(strip=True)
    else:
        description = ""

    # ── TAGS ──
    # Tags appear as links in a tag-list section on the page
    tags = []
    tag_list = soup.find("ul", class_="tag-list")
    if tag_list:
        for tag_link in tag_list.find_all("a"):
            tag_text = tag_link.get_text(strip=True)
            if tag_text:
                tags.append(tag_text)

    # ── RESOURCE LINKS ──
    # The "Data and Resources" section has links to downloads/files
    resource_links = []
    resource_section = soup.find("section", id="dataset-resources")
    if resource_section:
        for a_tag in resource_section.find_all("a", href=True):
            href = a_tag["href"]
            # Build full URL if it's a relative link
            if href.startswith("/"):
                href = BASE_URL + href
            # Only include actual resource links, skip anchors and nav links
            if "/resource/" in href or href.startswith("http"):
                if href not in resource_links:
                    resource_links.append(href)

    # ── LANDING PAGE ──
    # Found in the "Additional Info" metadata table
    landing_page = None
    info_table = soup.find("table", class_="table-striped")
    if info_table:
        for row in info_table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                label = th.get_text(strip=True).lower()
                if "landing" in label or "landingpage" in label:
                    # The value might be a link or plain text
                    link = td.find("a")
                    if link and link.get("href"):
                        landing_page = link["href"]
                    else:
                        landing_page = td.get_text(strip=True)

    return {
        "dataset_url": url,
        "title": title,
        "description": description,
        "tags": tags,
        "resource_links": resource_links,
        "landing_page": landing_page,
        "text_sources": [url] # Wraps the source URL in a list as required
    }


def main():
    # ── PARSE COMMAND LINE ARGUMENTS ──
    parser = argparse.ArgumentParser(
        description="Scrape NASA Open Data Portal datasets by tag"
    )
    parser.add_argument("--tag", required=True, help="Tag to search for (e.g. cassini)")
    parser.add_argument("--out", default="datasets.jsonl", help="Output JSONL file")
    args = parser.parse_args()

    print(f"=== NASA Open Data Scraper ===")
    print(f"Tag:    {args.tag}")
    print(f"Output: {args.out}")
    print()

    # ── STEP 1: COLLECT ALL DATASET LINKS FROM LISTING PAGES ──
    print("--- Step 1: Collecting dataset links from listing pages ---")
    all_dataset_urls = []
    page_num = 1

    while True:
        print(f"\n  Page {page_num}:")
        links = get_dataset_links(args.tag, page_num)

        if not links:
            print("  No more datasets found. Done collecting links.")
            break

        all_dataset_urls.extend(links)
        print(f"  Found {len(links)} datasets (total so far: {len(all_dataset_urls)})")
        page_num += 1

    print(f"\nTotal dataset links collected: {len(all_dataset_urls)}")

    # ── STEP 2: VISIT EACH DATASET PAGE AND EXTRACT DATA ──
    print("\n--- Step 2: Scraping individual dataset pages ---")
    records_written = 0

    with open(args.out, "w", encoding="utf-8") as f:
        for i, dataset_url in enumerate(all_dataset_urls, start=1):
            print(f"\n  [{i}/{len(all_dataset_urls)}] Scraping: {dataset_url}")

            record = scrape_dataset(dataset_url)

            if record:
                # Write one JSON object per line (JSONL format)
                json_line = json.dumps(record, ensure_ascii=False)
                f.write(json_line + "\n")
                records_written += 1
                print(f"    ✓ Saved: {record['title'][:60]}...")
            else:
                print(f"    ✗ Failed to scrape, skipping.")

    # ── DONE ──
    print(f"\n=== Complete! ===")
    print(f"Records written: {records_written}")
    print(f"Output file: {args.out}")


if __name__ == "__main__":
    main()
