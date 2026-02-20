FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r requirements.txt -r backend/requirements.txt

# Copy application code
COPY tokenizer/ ./tokenizer/
COPY model/ ./model/
COPY backend/ ./backend/
COPY data/ ./data/

# Copy training scripts
COPY train_tokenizer.py train_model.py ./

# Create directories for pipeline output (gitignored, so not in repo)
RUN mkdir -p data/raw data/processed models

# Run training pipeline (creates models from sample data)
RUN python data/create_sample_dataset.py && \
    python data/preprocess.py && \
    python train_tokenizer.py && \
    python train_model.py

# Expose port (Railway/Render set PORT env var)
EXPOSE 8000

# Run with shell so $PORT is expanded; fallback to 8000 for local runs
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
