FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY tokenizer/ ./tokenizer/
COPY model/ ./model/
COPY backend/ ./backend/

# Copy trained models (should be built during CI/CD or mounted as volume)
COPY models/ ./models/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
