FROM python:3.11-slim

# Install ffmpeg and other system deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg build-essential nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip
RUN pip install -r /app/requirements.txt

# Copy application source
COPY . /app

# Default command — Railway will provide TOKEN via environment variable
CMD ["python", "main.py"]
