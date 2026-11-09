# Production Deployment Guide

## 1. Local Python Environment Deployment

### Step 1: Create and Activate Virtual Environment
```bash
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Linux / macOS:
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Run Tests
```bash
pytest
```

### Step 4: Launch Web Server
```bash
# Development:
python run.py

# Production with Gunicorn (Linux/Docker):
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 run:app
```

---

## 2. Docker & Containerized Deployment

### Step 1: Build Docker Image
```bash
docker build -t house-price-prediction:v1 .
```

### Step 2: Run Container
```bash
docker run -d -p 5000:5000 --name house-price-app house-price-prediction:v1
```

### Step 3: Launch with Docker Compose
```bash
docker compose up -d
```
The application will be live at `http://localhost:5000`.
Health check: `curl http://localhost:5000/api/health`

