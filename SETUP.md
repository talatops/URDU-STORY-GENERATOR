# Setup Guide

Complete setup instructions for the Urdu Story Generation System.

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Internet connection (for data collection)
- Docker (optional, for containerized deployment)

## Quick Start

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

### 2. Collect and Process Data

**Option A: Use Sample Dataset (Quick Testing)**
```bash
python3 data/create_sample_dataset.py
python3 data/preprocess.py
```

**Option B: Scrape from Website**
```bash
python3 data/scraper.py
python3 data/preprocess.py
```

**Option C: Use Complete Pipeline**
```bash
python3 run_pipeline.py
```

### 3. Train Models

```bash
# Train BPE tokenizer
python3 train_tokenizer.py

# Train trigram model
python3 train_model.py
```

### 4. Start Backend

```bash
cd backend
uvicorn main:app --reload
```

Backend will be available at `http://localhost:8000`

### 5. Start Frontend

```bash
cd frontend
cp .env.local.example .env.local
# Edit .env.local and set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Docker Deployment

### Build Backend Image

```bash
docker build -t urdu-story-backend -f backend/Dockerfile .
```

### Run Backend Container

```bash
docker run -p 8000:8000 urdu-story-backend
```

## Production Deployment

### Backend (Render/Railway)

1. Push code to GitHub
2. Connect repository to Render/Railway
3. Configure build settings:
   - Build command: `docker build -t urdu-story-backend -f backend/Dockerfile .`
   - Start command: `docker run -p $PORT:8000 urdu-story-backend`
4. Ensure `models/` directory is included in deployment

### Frontend (Vercel)

1. Connect GitHub repository to Vercel
2. Set environment variable: `NEXT_PUBLIC_API_URL` = your backend URL
3. Deploy automatically on push to main branch

## Troubleshooting

### Data Collection Issues

- **Scraper finds 0 stories**: Website structure may have changed. See `DATA_COLLECTION.md` for alternatives.
- **Network errors**: Check internet connection and website accessibility.

### Model Training Issues

- **Out of memory**: Reduce corpus size or use a machine with more RAM
- **Tokenizer training slow**: Normal for large vocabularies. Be patient.

### Backend Issues

- **Models not found**: Ensure `models/tokenizer.json` and `models/trigram.json` exist
- **Import errors**: Check Python path and module structure

### Frontend Issues

- **API connection failed**: Check `NEXT_PUBLIC_API_URL` in `.env.local`
- **CORS errors**: Ensure backend CORS is configured correctly

## File Structure

```
Aimen/
├── data/              # Data collection and preprocessing
├── tokenizer/         # BPE tokenizer implementation
├── model/             # Trigram language model
├── backend/           # FastAPI service
├── frontend/          # Next.js frontend
├── models/            # Trained models (generated)
└── requirements.txt   # Python dependencies
```

## Next Steps

1. Collect real Urdu stories for better model quality
2. Tune interpolation parameters (λ1, λ2, λ3) for better generation
3. Add more features to frontend (history, favorites, etc.)
4. Implement model evaluation metrics
5. Add unit tests for all components
