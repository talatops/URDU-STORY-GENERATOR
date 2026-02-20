# Data Collection Guide

## Primary Method: Web Scraping

The system is designed to scrape Urdu children's stories from UrduPoint Kids website.

### Running the Scraper

```bash
python3 data/scraper.py
```

The scraper will:
1. Visit UrduPoint Kids story listing pages
2. Extract story URLs
3. Scrape individual story content
4. Save to `data/raw/stories.json`

### Requirements

- Internet connection
- Python packages: `requests`, `beautifulsoup4`, `lxml`

### Troubleshooting

If scraping fails:

1. **Check website accessibility**: Visit https://www.urdupoint.com/kids/section/stories.html manually
2. **Website structure changed**: The website HTML structure may have changed. Update selectors in `data/scraper.py`
3. **Rate limiting**: The website may be blocking requests. Increase delay in scraper
4. **Network issues**: Check your internet connection

## Alternative Methods

### Option 1: Sample Dataset (Testing)

For testing purposes, use the sample dataset generator:

```bash
python3 data/create_sample_dataset.py
```

This creates a minimal dataset with 200 stories for testing the pipeline.

### Option 2: Manual Dataset

1. Collect Urdu stories from various sources
2. Format as JSON:

```json
[
  {
    "title": "Story Title",
    "content": "Story text here...",
    "category": "moral",
    "url": "source_url"
  }
]
```

3. Save to `data/raw/stories.json`

### Option 3: Alternative Sources

Consider these Urdu text sources:

1. **Hugging Face Datasets**:
   - Search for "Urdu" or "Urdu stories" datasets
   - Download and convert to required format

2. **Urdu Literature Corpus**:
   - Mozilla Data Collective: Urdu Literature Corpus
   - Contains stories and literature

3. **Other Urdu Websites**:
   - Adapt scraper for other Urdu story websites
   - Ensure content is children-appropriate

## Dataset Requirements

- **Minimum**: 200 stories
- **Format**: JSON with `title`, `content`, `category` fields
- **Language**: Urdu script (not Roman Urdu)
- **Content**: Children's stories (moral, educational, entertaining)

## Preprocessing

After collecting data, run preprocessing:

```bash
python3 data/preprocess.py
```

This will:
1. Clean HTML/ads
2. Normalize Unicode
3. Remove non-Urdu characters
4. Insert special tokens (<EOS>, <EOP>, <EOT>)
5. Output to `data/processed/corpus.txt`
