# Urdu Children's Story Generation System

A full-stack AI system that generates Urdu children's stories using classical NLP techniques (BPE tokenization and trigram language models) with modern software engineering practices.

## Architecture

- **Data Collection**: Web scraping from UrduPoint Kids (200+ stories)
- **Preprocessing**: HTML removal, Urdu-focused cleaning, deduplication, quality filters
- **Tokenizer**: Word-level tokenizer (Urdu-suited, ~1500 vocab) for cleaner generation
- **Language Model**: Trigram model with Maximum Likelihood Estimation and linear interpolation
- **Backend**: FastAPI microservice with Docker containerization
- **Frontend**: Next.js ChatGPT-like interface with streaming support
- **Deployment**: Vercel (frontend) + Render/Railway (backend)

## Project Structure

```
Ello/
├── data/                 # Data collection and preprocessing
│   ├── scraper.py       # Web scraper for Urdu stories
│   └── preprocess.py    # Preprocessing pipeline
├── tokenizer/           # Urdu tokenizers
│   ├── word_tokenizer.py  # Word-level (default)
│   ├── bpe.py             # BPE (legacy)
│   └── loader.py          # Auto-detect tokenizer type
├── model/               # Trigram language model
│   └── trigram.py
├── backend/             # FastAPI service
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/            # Next.js frontend
├── train_tokenizer.py   # Train word tokenizer
├── train_model.py       # Train trigram model
└── requirements.txt     # Python dependencies
```

## Setup Instructions

### 1. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt
pip install -r backend/requirements.txt

# Frontend dependencies
cd frontend
npm install
```

### 2. Data Collection and Preprocessing

```bash
# Scrape Urdu stories (minimum 200)
python data/scraper.py

# Preprocess and create corpus
python data/preprocess.py
```

### 3. Train Models

```bash
# Train BPE tokenizer
python train_tokenizer.py

# Train trigram model
python train_model.py
```

### 4. Run Backend

```bash
cd backend
uvicorn main:app --reload
```

Or with Docker:
```bash
docker build -t urdu-story-backend -f backend/Dockerfile .
docker run -p 8000:8000 urdu-story-backend
```

### 5. Run Frontend

```bash
cd frontend
cp .env.local.example .env.local
# Edit .env.local to set NEXT_PUBLIC_API_URL
npm run dev
```

## API Endpoints

### POST /generate
Generate a complete story from a prefix.

**Request:**
```json
{
  "prefix": "ایک بار ایک بادشاہ تھا",
  "max_length": 500,
  "temperature": 1.0
}
```

**Response:**
```json
{
  "story": "generated story text...",
  "tokens_generated": 150
}
```

### GET /generate/stream
Stream story generation token-by-token (Server-Sent Events).

**Query Parameters:**
- `prefix`: Starting phrase
- `max_length`: Maximum generation length (default: 500)
- `temperature`: Sampling temperature (default: 1.0)

## Deployment

### Backend (Render/Railway)

1. Push code to GitHub
2. Connect repository to Render/Railway
3. Set build command: `docker build -t urdu-story-backend -f backend/Dockerfile .`
4. Set start command: `docker run -p $PORT:8000 urdu-story-backend`
5. Ensure models are included in the build or mounted as volumes

### Frontend (Vercel)

1. Connect GitHub repository to Vercel
2. Set `NEXT_PUBLIC_API_URL` environment variable to backend URL
3. Deploy automatically on push to main branch

## Special Tokens

- `<EOS>` (U+E001): End of Sentence
- `<EOP>` (U+E002): End of Paragraph  
- `<EOT>` (U+E003): End of Story

## License

This project is for educational purposes.
