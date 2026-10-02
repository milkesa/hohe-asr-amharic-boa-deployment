# Troubleshooting & FAQ - Hohe ASR Amharic Docker Deployment

---

## Troubleshooting Guide

### Container Won't Start

**Symptom**: `docker-compose up` fails immediately

**Solutions**:
```bash
# 1. Check Docker is running
docker --version
systemctl status docker  # Linux

# 2. Check for port conflicts
sudo lsof -i :8000
sudo lsof -i :80
sudo lsof -i :443

# 3. Rebuild without cache
docker-compose down
docker-compose build --no-cache
docker-compose up

# 4. Check logs for errors
docker-compose logs hohe-asr-api
```

---

### Model Takes Too Long to Load

**Symptom**: Container starts but model loading takes 5+ minutes

**Causes & Solutions**:

```bash
# 1. First-time download is slow (normal)
# Expected: 30-60 seconds on broadband, 2-3 minutes on slower connections
docker-compose logs -f hohe-asr-api | grep -i "loading\|downloading"

# 2. Pre-download model for faster startup (recommended)
mkdir -p ./models
python3 << 'EOF'
import os
os.environ['HF_HOME'] = './models'
from transformers import AutoModelForCTC, AutoProcessor
AutoModelForCTC.from_pretrained("snapwre/hohe-asr-amharic")
AutoProcessor.from_pretrained("snapwre/hohe-asr-amharic")
print("✓ Model cached in ./models directory")
EOF

# 3. Use GPU for faster inference (if available)
# Install: nvidia-docker, GPU-enabled PyTorch

# 4. Check network speed
speedtest-cli
```

---

### Out of Memory (OOM) Errors

**Symptom**: Container restarts or `Cannot allocate memory` errors

```bash
# 1. Check current memory usage
docker stats hohe-asr-api

# 2. Increase memory limit in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 16G  # Increase from 8G
    reservations:
      memory: 8G

# 3. Restart container
docker-compose down
docker-compose up -d

# 4. Check system has available memory
free -h
df -h

# 5. If system memory is low, process smaller batches
# Max: 1 concurrent request per 8GB RAM
```

---

### API Responds Slowly

**Symptom**: `/transcribe` endpoint takes 30+ seconds

```bash
# 1. Check CPU usage
docker stats --no-stream hohe-asr-api

# 2. Increase CPU allocation
deploy:
  resources:
    limits:
      cpus: '4'  # Increase from 2

# 3. Check if using GPU
curl http://localhost:8000/info | grep device
# Expected: "device": "cuda:0" (for GPU) or "cpu"

# 4. Increase PyTorch thread count
# Add to Dockerfile:
# ENV OMP_NUM_THREADS=4
# ENV MKL_NUM_THREADS=4

# 5. Verify audio file isn't too long (test with 10-30 sec audio)
```

---

### API Not Responding / Connection Refused

**Symptom**: `curl: (7) Failed to connect to localhost port 8000`

```bash
# 1. Verify container is running
docker-compose ps
docker ps | grep hohe-asr

# 2. Check if process is listening on port 8000
netstat -tulpn | grep 8000
ss -tulpn | grep 8000

# 3. Check container logs for startup errors
docker-compose logs hohe-asr-api --tail 50

# 4. Try connecting from inside container
docker-compose exec hohe-asr-api curl localhost:8000/health

# 5. Check if port is mapped correctly
docker-compose ps  # Should show 0.0.0.0:8000->8000/tcp

# 6. If behind firewall/proxy, check port forwarding
ping localhost
ping 127.0.0.1
```

---

### Model Download Fails

**Symptom**: `Failed to download model` or `Connection timeout`

```bash
# 1. Check internet connection
curl https://huggingface.co -I

# 2. Check Hugging Face API is accessible
python3 << 'EOF'
from huggingface_hub import list_repo_files
files = list_repo_files("snapwre/hohe-asr-amharic")
print(f"✓ Model accessible, {len(files)} files")
EOF

# 3. Check DNS resolution
nslookup huggingface.co
dig huggingface.co

# 4. If behind proxy, set proxy environment
docker-compose exec -e HTTP_PROXY="http://proxy:port" hohe-asr-api bash

# 5. Pre-download model outside container and mount
# See "Model Takes Too Long" solution above

# 6. Check HF token (if model is private)
cat ~/.cache/huggingface/token
```

---

### Audio Format Not Supported

**Symptom**: `Transcription failed: Invalid audio format` or `librosa error`

```bash
# 1. Verify audio file format
file audio.wav
ffprobe audio.wav

# 2. Check supported formats in app.py
# Supported: WAV, MP3, FLAC, OGG

# 3. Convert audio to WAV
ffmpeg -i audio.mp3 -acodec pcm_s16le -ar 16000 audio.wav

# 4. Check audio properties
ffmpeg -i audio.wav
# Look for: PCM 16-bit, Mono, 16000 Hz (ideal)

# 5. Test with known-good audio
# For testing, use sample from: 
# https://github.com/mozilla/common-voice

# 6. If audio is corrupted
ffmpeg -i audio.wav -c:a libmp3lame audio_fixed.wav
```

---

### Disk Space Issues

**Symptom**: `No space left on device`

```bash
# 1. Check disk usage
df -h
du -sh ./models
du -sh ~/docker_volumes

# 2. Clean up Docker
docker system prune
docker system prune -a  # More aggressive

# 3. Remove old model versions (if using local models)
rm -rf ./models/transformers/snapwre/*/snapshots/*
# Keep only 1 most recent snapshot

# 4. Move models to larger disk/partition
mv ./models /path/to/larger/disk/models
# Update docker-compose.yml volume mount

# 5. Clear temporary files
docker-compose down -v
docker volume prune
```

---

### CORS Errors in Browser

**Symptom**: `No 'Access-Control-Allow-Origin' header`

```bash
# 1. Verify CORS is enabled in app.py (should be by default)
# Check: CORSMiddleware configuration

# 2. If using nginx, ensure CORS headers are passed
# In nginx.conf, add:
location / {
    add_header 'Access-Control-Allow-Origin' '*' always;
    proxy_pass http://asr_backend;
}

# 3. For testing without CORS (development only)
curl -H "Origin: http://localhost:3000" http://localhost:8000/

# 4. Restrict CORS in production
# Update app.py:
CORSMiddleware(
    allow_origins=["https://your-domain.com"],  # Specific domains only
    ...
)
```

---

## FAQ - Frequently Asked Questions

### Q1: How much disk space does the model need?
**A**: The model weights are approximately 2-3GB. Total container image with dependencies is ~4-5GB.

### Q2: Can I use this on AWS/GCP/Azure?
**A**: Yes! Deploy using:
- **AWS EC2**: Use Ubuntu 22.04 AMI with Docker pre-installed
- **AWS ECS/Fargate**: Push image to ECR, deploy via Fargate
- **GCP Compute Engine**: Use Container-Optimized OS
- **Azure Container Instances**: Use Docker image
- **Kubernetes**: Use provided deployment.yaml

### Q3: What audio sample rate is required?
**A**: Any rate works (8kHz to 48kHz). The application auto-resamples to 16kHz internally.

### Q4: Can I use this for real-time transcription?
**A**: Yes, but with latency (1-5 seconds depending on audio length). For live streaming:
- Buffer audio in 10-second chunks
- Send chunks to API
- Stream results back

### Q5: How do I add authentication?
```python
# In app.py, add:
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    credentials: HTTPAuthCredentials = Depends(security)
):
    if credentials.credentials != "YOUR_SECRET_TOKEN":
        raise HTTPException(status_code=403, detail="Invalid token")
    # ... rest of transcription code
```

### Q6: How do I scale to handle multiple requests?
**A**: Use docker-compose with multiple instances:
```yaml
services:
  hohe-asr-api-1:
    build: .
    ports: ["8001:8000"]
  hohe-asr-api-2:
    build: .
    ports: ["8002:8000"]
  hohe-asr-api-3:
    build: .
    ports: ["8003:8000"]
  nginx:
    # Load balances across all 3 instances
```

### Q7: How do I monitor production?
**A**: 
```bash
# Monitor resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Monitor API performance
watch -n 1 'curl -s http://localhost:8000/health | jq'

# Set up logging
docker-compose logs -f > api.log
```

### Q8: What if I get "No module named 'torch'"?
**A**: Requirements.txt may not have installed correctly:
```bash
docker-compose down
docker volume prune
docker-compose build --no-cache
docker-compose up -d
```

### Q9: How do I use GPU acceleration?
**A**: 
```bash
# 1. Install nvidia-docker
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2

# 2. Update docker-compose.yml
services:
  hohe-asr-api:
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all

# 3. Update requirements.txt
# Change: torch==2.1.0
# To: torch==2.1.0+cu118

# 4. Rebuild and run
docker-compose build --no-cache
docker-compose up -d

# 5. Verify GPU is being used
curl http://localhost:8000/info | grep device
# Should show: "device": "cuda:0"
```

### Q10: How do I backup the model?
**A**:
```bash
# Backup the models directory
tar -czf hohe-asr-model-backup.tar.gz ./models

# Or copy to cloud storage
gsutil -m cp -r ./models gs://your-bucket/hohe-asr-backup
aws s3 sync ./models s3://your-bucket/hohe-asr-backup
```

### Q11: Can I run multiple different models?
**A**: Yes, with modifications:
```python
# In app.py, load multiple models
model_amharic = AutoModelForCTC.from_pretrained("snapwre/hohe-asr-amharic")
model_oromo = AutoModelForCTC.from_pretrained("path/to/oromo-asr")

# Add endpoint parameter
@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: str = Query("amharic", enum=["amharic", "oromo"])
):
    model = model_amharic if language == "amharic" else model_oromo
    # ... transcription code
```

### Q12: What's the typical response time?
**A**: 
- Health check: <1ms
- Model loading: 30-60s (first run)
- Single file transcription: 1-5s (depending on audio length)
- Batch (10 files): 10-50s

### Q13: How do I update to a newer model version?
**A**:
```bash
# 1. Update model name in app.py
# Change: "snapwre/hohe-asr-amharic"
# To: "snapwre/hohe-asr-amharic-v2" (if available)

# 2. Rebuild and redeploy
docker-compose build --no-cache
docker-compose up -d
```

### Q14: Can I use this offline?
**A**: No, first-time model download requires internet. After download:
- The model is cached in `/models`
- Subsequent runs work offline
- For fully offline: pre-download and mount the models directory

### Q15: How do I troubleshoot transcription accuracy?
**A**:
```bash
# Test with various audio samples
# Check sample rate
ffprobe -show_entries format=sample_rate audio.wav

# Ensure Amharic audio (not English, etc.)
# Check audio quality (no heavy background noise)

# If accuracy is poor:
# 1. Try another Amharic ASR model
# 2. Pre-process audio (noise reduction, normalization)
# 3. Consider fine-tuning on your specific use case
```

---

## Getting Help

### Debug Information to Collect

```bash
# System info
uname -a
docker --version
docker-compose --version

# Container info
docker-compose ps -a
docker logs hohe-asr-api
docker inspect hohe-asr-amharic

# API health
curl -v http://localhost:8000/health

# Resource usage
docker stats --no-stream

# Model info
curl http://localhost:8000/info
```

### Useful Resources

- **Hugging Face Model Card**: https://huggingface.co/snapwre/hohe-asr-amharic
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Docker Documentation**: https://docs.docker.com/
- **PyTorch Troubleshooting**: https://pytorch.org/
- **Librosa Audio**: https://librosa.org/

### Reporting Issues

When reporting issues, include:
1. System specs (OS, RAM, CPU, GPU)
2. Docker/Docker-compose versions
3. Complete error message (not just the summary)
4. Steps to reproduce
5. Debug information (from above)
6. docker-compose logs output

---

**Last Updated**: 2026-09-28  
**Version**: 1.0.0
