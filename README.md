# Web-Scraper-Example
This is everything you need to learn how to get data from Nasa.gov
Created for a homework in CSC 4641 NLP

# NASA Open Data Portal Scraper

## How to Run

### Prerequisites

Install the required Python libraries:

```bash
pip install requests beautifulsoup4
```

### Usage

```bash
python crawl.py --tag <TAG> --out <OUTPUT_FILE>
```

Example:

```bash
python crawl.py --tag mars --out datasets.jsonl
```

### Arguments

| Argument | Required | Description                          | Default          |
|----------|----------|--------------------------------------|------------------|
| `--tag`  | Yes      | The tag to search for (e.g. cassini) | —                |
| `--out`  | No       | Output JSONL filename                | datasets.jsonl   |

## Output Format

Each line of the output file is a JSON object with these fields:

```json
{
  "dataset_url": "https://data.nasa.gov/dataset/some-dataset-slug",
  "title": "Dataset Title",
  "description": "Description text...",
  "tags": ["tag1", "tag2"],
  "resource_links": ["https://..."],
  "landing_page": "https://..." or null,
  "text_sources": ["https://..."]
}
```

## Assumptions

- The NASA Open Data Portal uses standard CKAN HTML structure.
- Title is in an `<h1>` tag on dataset detail pages.
- Description is in a `<div class="notes">` on dataset detail pages.
- Tags are in a `<ul class="tag-list">` on dataset detail pages.
- Resources are in a `<section id="dataset-resources">`.
- Landing page (if present) is in the "Additional Info" table.
- Each listing page shows ~20 results (CKAN default).
- Pagination stops when a page returns zero dataset links.

## Ethical Scraping

- Rate limited to 1 request per second.
- Duplicate URLs are never fetched twice (tracked via a `seen_urls` set).
- Errors are handled gracefully — the scraper logs failures and continues.

## Known Issues
- During the crawl, a small percentage of requests (approx. 8%) timed out due to server-side latency. The scraper is designed to catch these RequestExceptions,   log the error, and continue to the next record rather than crashing, ensuring partial data collection is preserved.

- CSS class names are based on CKAN defaults; if NASA customizes their
  theme, some selectors may need adjustment.
- Very large tags (thousands of datasets) will take a while due to the
  1-second rate limit — this is intentional and respectful.
- Some datasets may have no resources, description, or landing page.
  The scraper handles these gracefully (empty lists or null values).

