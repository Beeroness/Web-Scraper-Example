# SPEC.md — NASA Open Data Portal Recon

## Data Source

NASA Open Data Portal (CKAN-based): <https://data.nasa.gov/dataset/>

## Chosen Tag

`cassini` (Cassini–Huygens mission datasets)

---

## 1. URL Pattern for Listing Datasets by Tag

```
https://data.nasa.gov/dataset/?tags=<TAG>
```

Example:

```
https://data.nasa.gov/dataset/?tags=cassini
```

Multiple tags can be combined:

```
https://data.nasa.gov/dataset/?tags=cassini-huygens&tags=saturn
```

## 2. Pagination

CKAN appends a `page` query parameter (1-indexed):

```
https://data.nasa.gov/dataset/?tags=<TAG>&page=<N>
```

Example:

```
https://data.nasa.gov/dataset/?tags=cassini&page=1
https://data.nasa.gov/dataset/?tags=cassini&page=2
```

The default results-per-page for CKAN is 20. Scraping should continue
incrementing the page number until a page returns zero dataset links.

## 3. Dataset Detail Page

Each dataset's detail URL follows the slug pattern:

```
https://data.nasa.gov/dataset/<slug>
```

Example:

```
https://data.nasa.gov/dataset/cassini-high-rate-detector-v11-0
```

### Field Locations in HTML (confirmed via DevTools)

| Field              | Where to Find It                                                                                               |
|--------------------|----------------------------------------------------------------------------------------------------------------|
| **Title**          | `<h1>` tag (confirmed via Inspect on dataset detail page).                                                     |
| **Description**    | `<div class="notes embedded-content">` containing `<p>` tags with the description text (confirmed via Inspect).|
| **Tags**           | Tag list in the sidebar — each tag is an `<a>` link inside a list element (standard CKAN convention).          |
| **Resource Links** | "Data and Resources" section — contains `<a>` tags with `href` pointing to resource/download URLs.             |
| **Landing Page**   | "Additional Info" table — look for a row labeled `landing_page` or `Landing Page`; value cell has the URL.     |
| **Other Metadata** | "Additional Info" table also contains fields like `source`, `publisher`, `modified`, `identifier`, etc.        |

## 4. Resource Page Pattern

Individual resources can be accessed at:

```
https://data.nasa.gov/dataset/<slug>/resource/<resource-id>
```

These pages contain a direct download button/link and resource metadata (format, size, etc.).

## 5. Scraping Strategy

1. Start at the tag listing page for the chosen tag.
2. On each listing page, collect all dataset detail-page URLs (the `<a>` tags inside each dataset heading).
3. Increment the page number and repeat until no more datasets are found.
4. Visit each dataset detail page and extract: title, description, tags, resource links, landing page, and any other metadata.
5. Write each record as a single JSON line to `datasets.jsonl`.

## 6. Rate Limiting and Caching

- Insert a 1-second delay (`time.sleep(1)`) between HTTP requests.
- Maintain a `seen_urls` set to avoid re-downloading the same page.
