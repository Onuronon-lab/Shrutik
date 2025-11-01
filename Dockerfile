FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip config set global.timeout 1000 && \
    pip config set global.retries 5 && \
    pip install --no-cache-dir --default-timeout=1000 \
        numpy>=1.24.0 scipy>=1.11.0 && \
    pip install --no-cache-dir --default-timeout=1000 \
        librosa>=0.10.0 && \
    pip install --no-cache-dir --default-timeout=1000 \
        -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]