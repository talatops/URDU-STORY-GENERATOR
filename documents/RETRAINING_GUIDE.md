# Retraining the Model from Scratch

Complete step-by-step guide to retrain the Urdu Story Generator from dataset scraping to final model.

---

## Prerequisites

```bash
# Install dependencies (from project root)
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

---

## Step 1: Dataset Collection

You have **three options** for getting Urdu story data.

### Option A: Web Scraping (Real Data)

**Single-source scraper (UrduPoint):**
```bash
python data/scraper.py
```
- Scrapes from `urdupoint.com/kids/section/stories.html`
- Saves to `data/raw/stories.json`
- Requires internet; may need selector updates if the site changes

**Multi-platform scraper (more sources):**
```bash
python data/multi_platform_scraper.py
```
- Scrapes from multiple Urdu story websites
- Produces more diverse data
- Output: `data/raw/stories.json`

### Option B: Sample Dataset (Quick Testing)

For testing the pipeline without scraping:
```bash
python data/create_sample_dataset.py
```
- Creates ~200 sample stories in `data/raw/stories.json`
- No internet required
- Lower quality than real scraped data

### Option C: Manual Dataset

1. Create `data/raw/stories.json` with this format:
```json
[
  {
    "title": "Story Title",
    "content": "Full story text in Urdu...",
    "category": "moral",
    "url": "optional_source_url"
  }
]
```
2. Minimum **200 stories** recommended for decent results.

---

## Step 2: Preprocess the Corpus

```bash
python data/preprocess.py
```

**What it does:**
- Reads `data/raw/stories.json`
- Merges curated stories from `data/curated_classic_stories.json` (if present)
- Cleans HTML, normalizes Unicode, removes non-Urdu text
- Inserts special tokens (EOS, EOP, EOT)
- Outputs `data/processed/corpus.txt` (one story per line)

**Input:** `data/raw/stories.json`  
**Output:** `data/processed/corpus.txt`

---

## Step 3: Train the Tokenizer

```bash
python train_tokenizer.py
```

**What it does:**
- Loads `data/processed/corpus.txt`
- Trains a **word-level tokenizer** (optimized for Urdu)
- Saves `models/tokenizer.json`

**Input:** `data/processed/corpus.txt`  
**Output:** `models/tokenizer.json`

---

## Step 4: Train the Language Model

```bash
python train_model.py
```

**What it does:**
- Loads `models/tokenizer.json` and `data/processed/corpus.txt`
- Trains a **trigram** language model (MLE with interpolation)
- Saves `models/trigram.json`

**Input:** `models/tokenizer.json`, `data/processed/corpus.txt`  
**Output:** `models/trigram.json`

---

## Step 5: Run the Backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Or with reload for development:
```bash
uvicorn backend.main:app --reload --port 8000
```

---

## Full Pipeline (One Command)

To run everything in sequence (skips steps if output already exists):

```bash
python run_pipeline.py
```

**Note:** `run_pipeline.py` checks for existing files and skips steps. To retrain from scratch, **delete the outputs** first (see below).

---

## Retraining from Scratch (Clean Slate)

To force a complete retrain, remove all generated files:

```bash
# Remove raw data (optional - only if you want to re-scrape)
rm -rf data/raw/*

# Remove processed corpus
rm -rf data/processed/*

# Remove trained models
rm -f models/tokenizer.json models/trigram.json
```

Then run the full pipeline:

```bash
# 1. Scrape (or use sample)
python data/scraper.py
# OR: python data/multi_platform_scraper.py
# OR: python data/create_sample_dataset.py

# 2. Preprocess
python data/preprocess.py

# 3. Train tokenizer
python train_tokenizer.py

# 4. Train model
python train_model.py
```

---

## Pipeline Summary

| Step | Script | Input | Output |
|------|--------|-------|--------|
| 1a | `data/scraper.py` | — | `data/raw/stories.json` |
| 1b | `data/multi_platform_scraper.py` | — | `data/raw/stories.json` |
| 1c | `data/create_sample_dataset.py` | — | `data/raw/stories.json` |
| 2 | `data/preprocess.py` | `data/raw/stories.json` | `data/processed/corpus.txt` |
| 3 | `train_tokenizer.py` | `data/processed/corpus.txt` | `models/tokenizer.json` |
| 4 | `train_model.py` | `corpus.txt` + `tokenizer.json` | `models/trigram.json` |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Scraper finds 0 stories | Website structure may have changed; try `create_sample_dataset.py` or manual JSON |
| `stories.json not found` | Run Step 1 (scraper or sample) first |
| `corpus.txt not found` | Run `data/preprocess.py` after scraping |
| `tokenizer.json not found` | Run `train_tokenizer.py` after preprocessing |
| Out of memory during training | Use fewer stories or a machine with more RAM |
| Poor generation quality | Add more/better Urdu stories; aim for 500+ stories for better results |
