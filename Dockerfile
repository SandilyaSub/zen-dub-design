# Build stage for dependencies
FROM python:3.9-slim AS builder

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements-minimal.txt .

# Upgrade pip and install dependencies with increased timeout
RUN pip install --upgrade pip && \
    pip install --no-cache-dir wheel && \
    pip wheel --no-cache-dir --wheel-dir=/app/wheels -r requirements-minimal.txt

# Add jiwer package explicitly
RUN pip wheel --no-cache-dir --wheel-dir=/app/wheels jiwer>=2.3.0

# Add sentence-transformers and sacrebleu packages explicitly
RUN pip wheel --no-cache-dir --wheel-dir=/app/wheels sentence-transformers>=2.2.2 sacrebleu>=2.3.1

# Add video processing packages explicitly
RUN pip wheel --no-cache-dir --wheel-dir=/app/wheels yt-dlp>=2023.3.4 pytube>=15.0.0 google-api-python-client>=2.100.0 youtube-dl-server>=0.3

# Runtime stage
FROM python:3.9-slim

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libasound2-dev \
    python3-dev \
    build-essential \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy wheels and requirements from builder stage
COPY --from=builder /app/wheels /app/wheels
COPY requirements-minimal.txt /app/

# Install Python packages
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --find-links=/app/wheels -r /app/requirements-minimal.txt && \
    pip install --no-cache-dir --find-links=/app/wheels jiwer>=2.3.0 sentence-transformers>=2.2.2 sacrebleu>=2.3.1 yt-dlp>=2023.3.4 pytube>=15.0.0 google-api-python-client>=2.100.0 youtube-dl-server>=0.3

# Copy preload script first
COPY utils/preload_models.py /app/utils/preload_models.py

# Pre-download BERT model and verify dependencies
RUN mkdir -p /root/.cache/torch/sentence_transformers && \
    python3 /app/utils/preload_models.py

# Verify yt-dlp installation
RUN python3 -c "import yt_dlp; print('yt-dlp version:', yt_dlp.version.__version__)"

# Copy application code
COPY . .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Suppress NNPACK warnings
ENV NNPACK_IGNORE_INCOMPATIBLE_CPU=1
ENV USE_NNPACK=0
ENV PYTHONWARNINGS="ignore::UserWarning"

# Set placeholder environment variables for API keys for local development
# These will be overridden by Secret Manager in production
# Note: For Gemini API, we use an empty string instead of placeholder to avoid API errors
ENV SARVAM_API_KEY="placeholder"
ENV GEMINI_API_KEY=""
ENV CARTESIA_API_KEY="placeholder"
ENV CARTESIA_API_VERSION="placeholder"
ENV YOUTUBE_API_KEY="placeholder"
ENV SECRET_KEY="placeholder"

# Expose port
EXPOSE 8080

# Command to run the application
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
