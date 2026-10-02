# Hohe ASR Amharic - Quick Reference

## Command Cheat Sheet

### Initial Setup (One-time)
```bash
# Create project directory
mkdir -p ~/hohe-asr-api && cd ~/hohe-asr-api

# Copy all provided files here
# Files needed: app.py, requirements.txt, Dockerfile, docker-compose.yml, 
#               .dockerignore, nginx.conf, test_api.py

# Build Docker image
docker-compose build
```

### Start/Stop Container
```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f hohe-asr-api

# Stop
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Testing
```bash
# Health check
curl http://localhost:8000/health

# Transcribe single file
curl -X POST http://localhost:8000/transcribe \
  -F "file=@audio.wav"

# Batch transcribe
curl -X POST http://localhost:8000/transcribe-batch \
  -F "files=@audio1.wav" -F "files=@audio2.wav"

# Run full test suite
python3 test_api.py
```

### Monitoring
```bash
# View container status
docker-compose ps

# Check resource usage
docker stats hohe-asr-api

# Check logs with tail
docker-compose logs -f --tail 50

# Container details
docker-compose exec hohe-asr-api cat /proc/self/limits
```

### Troubleshooting
```bash
# Restart container
docker-compose restart hohe-asr-api

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d

# Check what's using port 8000
sudo lsof -i :8000

# Clear all Docker data (CAREFUL!)
docker system prune -a
```

### Development
```bash
# Run locally without Docker (for testing)
pip install -r requirements.txt
python3 app.py

# Check model is loading (in Python)
python3 << 'EOF'
from transformers import AutoModelForCTC, AutoProcessor
model = AutoModelForCTC.from_pretrained("snapwre/hohe-asr-amharic")
processor = AutoProcessor.from_pretrained("snapwre/hohe-asr-amharic")
print("✓ Model loaded successfully")
EOF
```

---

## File Structure Required

```
hohe-asr-api/
├── app.py                    # Main API application
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container config
├── docker-compose.yml       # Docker orchestration
├── .dockerignore           # Files to exclude from image
├── nginx.conf              # Reverse proxy config
├── test_api.py             # Test script
├── DEPLOYMENT_STEPS.md     # Full guide (this was sent)
└── QUICK_REFERENCE.md      # This file
```

---

## API Endpoints Summary

| Endpoint | Method | Purpose | Input |
|----------|--------|---------|-------|
| `/` | GET | API info | - |
| `/health` | GET | Health check | - |
| `/info` | GET | Model info | - |
| `/transcribe` | POST | Single transcription | Audio file (form data) |
| `/transcribe-batch` | POST | Batch transcription | Multiple files (form data) |

---

## Performance Specs

| Metric | Value |
|--------|-------|
| Startup time | 30-60 seconds |
| Inference time | 1-5 seconds per 10 seconds of audio |
| Memory usage | 4-6 GB |
| CPU usage | 20-50% (1-2 cores) |
| Model size | ~2-3 GB |

---

## Environment Variables

```bash
# In docker-compose.yml or .env file
HF_HOME=/models                    # Model cache location
PYTHONUNBUFFERED=1               # Stream logs
PYTORCH_CUDA_ALLOC_CONF=...      # GPU memory settings (if using GPU)
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| Model loads slowly | Use GPU or pre-download model |
| Out of memory | Increase memory limit in docker-compose |
| Port 8000 in use | Change port mapping in docker-compose.yml |
| Model download fails | Check internet connection |
| Transcription errors | Check audio format/quality |
| API not responding | Check container logs |

---

## Integration Examples

### Python
```python
import requests

with open('audio.wav', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/transcribe',
        files={'file': f}
    )
    result = response.json()
    print(f"Transcription: {result['text']}")
```

### cURL
```bash
curl -X POST http://localhost:8000/transcribe \
  -F "file=@audio.wav" | jq '.text'
```

### JavaScript/Node.js
```javascript
const FormData = require('form-data');
const fs = require('fs');

const form = new FormData();
form.append('file', fs.createReadStream('audio.wav'));

fetch('http://localhost:8000/transcribe', {
  method: 'POST',
  body: form
})
.then(r => r.json())
.then(data => console.log(data.text));
```

---

## Deployment Locations

### Development
- Local machine with Docker
- Single container instance
- No HTTPS needed

### Testing/Staging
- Local server or VM
- 1-2 container instances
- Optional HTTPS with self-signed cert

### Production
- Cloud VM or Kubernetes
- 3+ container instances with load balancer
- HTTPS with valid certificate
- Authentication and rate limiting
- Monitoring and alerting

---

## Next Steps

1. **Download files** from the deployment guide
2. **Set up Docker** on your machine
3. **Run: `docker-compose build`**
4. **Run: `docker-compose up -d`**
5. **Test: `curl http://localhost:8000/health`**
6. **Transcribe: `curl -F "file=@audio.wav" http://localhost:8000/transcribe`**

---

## Documentation Files Provided

1. **hohe-asr-docker-deployment-guide.md** - Complete API code with explanations
2. **DEPLOYMENT_STEPS.md** - Step-by-step deployment instructions
3. **QUICK_REFERENCE.md** - This file
4. **Code files**:
   - `app.py` - FastAPI application
   - `requirements.txt` - Dependencies
   - `Dockerfile` - Container definition
   - `docker-compose.yml` - Service orchestration
   - `nginx.conf` - Reverse proxy
   - `test_api.py` - Testing script
   - `.dockerignore` - Docker exclusions

---

**Last Updated**: 2026-09-28  
**Ready for**: Development, Testing, Production
