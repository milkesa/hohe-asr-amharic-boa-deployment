# Hohe ASR Amharic - Complete Deployment Instructions

**Bank of Abyssinia AI CoE**  
**Date**: 2026-09-28  
**Status**: Production-Ready Guide

---

## Quick Start (5 minutes)

If you're familiar with Docker and just want to get running:

```bash
# 1. Clone/download files
mkdir hohe-asr && cd hohe-asr

# 2. Create files (see file list at end)
# Copy: Dockerfile, docker-compose.yml, requirements.txt, app.py, .dockerignore

# 3. Build and run
docker-compose up --build

# 4. Test
curl http://localhost:8000/health
```

---

## Full Step-by-Step Deployment

### STEP 1: Prepare Your Environment

#### 1.1 Check System Requirements

```bash
# Check Docker installation
docker --version
docker-compose --version

# Expected output:
# Docker version 20.10.x or higher
# docker-compose version 2.x or higher

# Check available disk space (need 4-6GB minimum)
df -h

# Check RAM (minimum 8GB, recommended 16GB)
free -h
```

#### 1.2 Create Project Directory

```bash
# Create and navigate to project directory
mkdir -p ~/hohe-asr-api
cd ~/hohe-asr-api

# Create subdirectories
mkdir -p models logs
```

#### 1.3 Check GPU Support (Optional)

For faster inference, you can use GPU acceleration:

```bash
# Check if NVIDIA GPU is available
nvidia-smi

# If GPU available, you can modify requirements.txt:
# Replace: torch==2.1.0
# With: torch==2.1.0+cu118

# And update Dockerfile to use CUDA base image:
# FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04
```

---

### STEP 2: Download and Organize Files

All required files are provided:

1. **app.py** - FastAPI application
2. **requirements.txt** - Python dependencies
3. **Dockerfile** - Container configuration
4. **docker-compose.yml** - Multi-container orchestration
5. **.dockerignore** - Files to exclude from Docker image
6. **nginx.conf** - Reverse proxy configuration
7. **test_api.py** - API testing script

**Directory structure after copying files:**

```
~/hohe-asr-api/
├── app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── nginx.conf
├── test_api.py
├── models/                 # For pre-downloaded models (optional)
├── logs/                   # For container logs
└── ssl/                    # For SSL certificates (optional)
```

---

### STEP 3: Build the Docker Image

#### 3.1 Build Using Docker Compose (Recommended)

```bash
# Navigate to project directory
cd ~/hohe-asr-api

# Build the image
docker-compose build

# Expected output:
# Building hohe-asr-api
# ...
# Successfully tagged hohe-asr-amharic:latest
```

#### 3.2 Alternative: Build Using Docker CLI

```bash
docker build -t hohe-asr-amharic:1.0 .

# Verify image was created
docker images | grep hohe-asr
```

#### 3.3 Verify Build Success

```bash
# Check image details
docker image inspect hohe-asr-amharic:latest

# Check image size
docker images hohe-asr-amharic
```

---

### STEP 4: Start the Container

#### 4.1 Using Docker Compose (Recommended)

```bash
# Start services in foreground (for testing)
docker-compose up

# Or start in background (for production)
docker-compose up -d

# View logs
docker-compose logs -f hohe-asr-api

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

#### 4.2 Using Docker CLI

```bash
# Create models volume
docker volume create asr_models

# Run container
docker run -d \
  --name hohe-asr-amharic \
  -p 8000:8000 \
  -v asr_models:/models \
  -e HF_HOME=/models \
  -e PYTHONUNBUFFERED=1 \
  --memory=8g \
  --cpus=2 \
  hohe-asr-amharic:1.0

# Check container status
docker ps | grep hohe-asr
```

#### 4.3 Verify Container is Running

```bash
# Check container logs (wait 30-60s for model to load)
docker-compose logs hohe-asr-api

# Or with Docker CLI
docker logs hohe-asr-amharic

# Expected output (after ~30s):
# INFO:     Application startup complete
```

---

### STEP 5: Verify the API is Working

#### 5.1 Health Check Endpoint

```bash
# Simple health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","model_loaded":true,"device":"cpu"}
```

#### 5.2 Info Endpoint

```bash
# Get model information
curl http://localhost:8000/info

# Expected response:
# {
#   "model_name": "hohe-asr-amharic",
#   "model_id": "snapwre/hohe-asr-amharic",
#   "task": "automatic-speech-recognition",
#   "language": "Amharic",
#   "device": "cpu",
#   "framework": "PyTorch with Hugging Face Transformers"
# }
```

#### 5.3 Root Endpoint

```bash
# API information
curl http://localhost:8000/

# Expected response shows available endpoints
```

#### 5.4 Full Test Suite

```bash
# Run the provided test script
python3 test_api.py

# Or test transcription with an audio file
python3 test_api.py /path/to/amharic_audio.wav

# Expected output:
# ✓ Health Check: PASSED
# ✓ Root Endpoint: PASSED
# ✓ Model Info: PASSED
```

---

### STEP 6: Test Transcription

#### 6.1 Basic Transcription Test

```bash
# Transcribe a single audio file
curl -X POST "http://localhost:8000/transcribe" \
  -F "file=@/path/to/audio.wav"

# Expected response:
# {
#   "text": "ሰላም ዓለም",
#   "confidence": null,
#   "model": "snapwre/hohe-asr-amharic",
#   "language": "am"
# }
```

#### 6.2 Batch Transcription

```bash
# Transcribe multiple files
curl -X POST "http://localhost:8000/transcribe-batch" \
  -F "files=@audio1.wav" \
  -F "files=@audio2.wav" \
  -F "files=@audio3.wav"

# Expected response:
# {
#   "results": [
#     {"filename": "audio1.wav", "text": "...", "status": "success"},
#     {"filename": "audio2.wav", "text": "...", "status": "success"},
#     ...
#   ],
#   "total": 3
# }
```

#### 6.3 Test with Python Script

```bash
#!/usr/bin/env python3
import requests

# Single file transcription
with open('test_audio.wav', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/transcribe',
        files=files,
        timeout=30
    )
    print(response.json())
```

---

### STEP 7: Production Deployment

#### 7.1 Enable HTTPS with Let's Encrypt

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Update nginx.conf with SSL paths
# ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

# Mount SSL directory in docker-compose
volumes:
  - /etc/letsencrypt:/etc/nginx/ssl:ro
```

#### 7.2 Configure Resource Limits

Update `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 16G
    reservations:
      cpus: '2'
      memory: 8G
```

#### 7.3 Set Up Logging

```bash
# Create log directory
mkdir -p logs

# Update docker-compose to mount logs
volumes:
  - ./logs:/var/log/nginx

# View logs
tail -f logs/access.log
tail -f logs/error.log
```

#### 7.4 Auto-restart Configuration

```bash
# In docker-compose.yml
restart: unless-stopped

# Verify auto-restart
docker ps -a  # Check RESTART policy
```

---

### STEP 8: Manage Models and Storage

#### 8.1 Pre-download Model (Faster Startup)

```bash
# Create models directory
mkdir -p models

# Download model locally
python3 << 'EOF'
import os
os.environ['HF_HOME'] = './models'

from transformers import AutoModelForCTC, AutoProcessor
model = AutoModelForCTC.from_pretrained("snapwre/hohe-asr-amharic")
processor = AutoProcessor.from_pretrained("snapwre/hohe-asr-amharic")
print("Model downloaded!")
EOF

# Then mount in docker-compose
volumes:
  - ./models:/models
```

#### 8.2 Monitor Model Cache Size

```bash
# Check models directory size
du -sh models/

# Clean up old model versions (be careful!)
cd models
rm -rf models/transformers/snapwre/hohe-asr-amharic/old_versions
```

#### 8.3 Update to Newer Model Version

```bash
# Remove old model (if caching locally)
rm -rf models/transformers/snapwre/hohe-asr-amharic

# Rebuild container
docker-compose build --no-cache
docker-compose up -d
```

---

### STEP 9: Monitor and Troubleshoot

#### 9.1 Container Health Monitoring

```bash
# Check container status
docker-compose ps

# View resource usage
docker stats hohe-asr-api

# Expected output:
# CONTAINER    CPU %   MEM USAGE
# hohe-asr-api 0.5%    4.2GB
```

#### 9.2 Common Issues and Solutions

**Issue: Model takes too long to load (> 2 minutes)**
```bash
# Solution: Pre-download model (see step 8.1) or use GPU
# Check device being used
curl http://localhost:8000/health | grep device
```

**Issue: Out of memory errors**
```bash
# Solution: Increase memory limit in docker-compose
deploy:
  resources:
    limits:
      memory: 16G
```

**Issue: Port 8000 already in use**
```bash
# Find process using port
sudo lsof -i :8000

# Change port in docker-compose
ports:
  - "8001:8000"
```

**Issue: Model fails to download**
```bash
# Check internet connection
curl https://huggingface.co

# Check HF tokens
cat ~/.cache/huggingface/token

# Try manual download
python3 -c "from transformers import AutoModel; AutoModel.from_pretrained('snapwre/hohe-asr-amharic')"
```

#### 9.3 View Application Logs

```bash
# Docker Compose logs
docker-compose logs -f hohe-asr-api --tail 100

# Full container logs
docker logs hohe-asr-amharic -f

# Nginx logs (if using)
docker-compose logs -f nginx
```

---

### STEP 10: Scaling for Production

#### 10.1 Load Balancing with Multiple Instances

```yaml
# docker-compose.yml
services:
  hohe-asr-api-1:
    build: .
    environment:
      - INSTANCE=1
    ports:
      - "8001:8000"

  hohe-asr-api-2:
    build: .
    environment:
      - INSTANCE=2
    ports:
      - "8002:8000"

  hohe-asr-api-3:
    build: .
    environment:
      - INSTANCE=3
    ports:
      - "8003:8000"

  nginx:
    # Nginx load balances across all instances
    depends_on:
      - hohe-asr-api-1
      - hohe-asr-api-2
      - hohe-asr-api-3
```

#### 10.2 Kubernetes Deployment (Optional)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hohe-asr-amharic
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hohe-asr
  template:
    metadata:
      labels:
        app: hohe-asr
    spec:
      containers:
      - name: hohe-asr-api
        image: hohe-asr-amharic:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "8Gi"
            cpu: "2"
          limits:
            memory: "16Gi"
            cpu: "4"
        env:
        - name: HF_HOME
          value: "/models"
        volumeMounts:
        - name: models
          mountPath: /models
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: asr-models-pvc
```

---

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/info` | Model information |
| POST | `/transcribe` | Transcribe single audio file |
| POST | `/transcribe-batch` | Transcribe multiple audio files |

### Request/Response Examples

**Single Transcription:**
```bash
curl -X POST http://localhost:8000/transcribe \
  -F "file=@audio.wav"
```

**Response:**
```json
{
  "text": "የመልካም ሰላም",
  "confidence": null,
  "model": "snapwre/hohe-asr-amharic",
  "language": "am"
}
```

### Supported Audio Formats

- WAV (.wav)
- MP3 (.mp3)
- FLAC (.flac)
- OGG (.ogg)

**Max file size**: 100MB  
**Sample rate**: Auto-resampled to 16kHz  
**Channels**: Mono (multi-channel auto-converted)

---

## Performance Tips

1. **Pre-download models** for faster startup
2. **Use GPU** if available (see Step 1.3)
3. **Batch requests** for multiple audio files
4. **Monitor resource usage** with `docker stats`
5. **Implement request queuing** for high volume

---

## Security Considerations

- ✅ Running as non-root user in container
- ✅ Health checks configured
- ✅ Resource limits enforced
- ✅ HTTPS support available (nginx + SSL)
- ⚠️ Add authentication for production (JWT/API keys)
- ⚠️ Restrict CORS origins in production
- ⚠️ Implement rate limiting

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_HOME` | `/models` | Model cache directory |
| `PYTHONUNBUFFERED` | `1` | Python buffering |
| `PYTORCH_CUDA_ALLOC_CONF` | `max_split_size_mb:512` | GPU memory config |

---

## File Checklist

Before deployment, ensure you have all files:

- [ ] app.py
- [ ] requirements.txt
- [ ] Dockerfile
- [ ] docker-compose.yml
- [ ] .dockerignore
- [ ] nginx.conf
- [ ] test_api.py
- [ ] This guide (DEPLOYMENT_STEPS.md)

---

## Support and Next Steps

### For Issues:
1. Check logs: `docker-compose logs -f`
2. Run health check: `curl http://localhost:8000/health`
3. Verify model load: Check device and model_loaded fields

### For Customization:
- Modify `app.py` to add authentication
- Update `nginx.conf` for SSL/domain configuration
- Adjust resource limits in `docker-compose.yml`
- Extend API with additional endpoints

### For Integration:
- Use `/transcribe` endpoint from your applications
- Implement request batching for efficiency
- Add error handling for failed transcriptions
- Monitor API response times and accuracy

---

**Last Updated**: 2026-09-28  
**Version**: 1.0.0  
**Status**: Production-Ready
