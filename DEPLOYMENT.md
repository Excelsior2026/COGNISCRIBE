# CogniScribe Deployment Guide

## 🚀 Quick Start (Docker Compose)

### Prerequisites
- Docker 20.10+ installed
- Docker Compose 2.0+ installed
- At least 8GB free disk space (for Ollama models)
- 4GB RAM minimum (8GB recommended)

### One-Command Deployment

```bash
# Clone repository
git clone https://github.com/Excelsior2026/COGNISCRIBE.git
cd COGNISCRIBE

# Start all services
docker compose up -d --build

# Watch logs (optional)
docker compose logs -f
```

**First startup takes 3-5 minutes** to download the Ollama model (~4.7GB).

---

## ✅ Verification

### Check Service Status
```bash
# View running containers
docker compose ps

# Expected output:
NAME                   STATUS              PORTS
cogniscribe-api        Up X minutes        0.0.0.0:8080->8080/tcp
cogniscribe-ollama     Up X minutes        0.0.0.0:11434->11434/tcp
```

### Test API Health
```bash
# Wait 2-3 minutes after startup, then:
curl http://localhost:8080/api/health

# Expected response:
{"status":"healthy","timestamp":"2026-01-03T22:57:00Z"}
```

### Test Ollama
```bash
curl http://localhost:11434/api/tags

# Should return list of models including llama3.1:8b
```

### Test Transcription (End-to-End)
```bash
# Upload a sample audio file
curl -X POST http://localhost:8080/api/pipeline \
  -F "file=@sample.mp3" \
  -F "ratio=0.15" \
  -F "subject=Test Lecture"

# Should return JSON with transcription and summary
```

---

## 🔧 Troubleshooting

### Issue: API Container Exits Immediately

**Symptom:**
```bash
docker compose ps
# Shows: cogniscribe-api   Exited (1)
```

**Solution:**
```bash
# Check logs for error
docker compose logs api

# Common causes:
# 1. Missing src/api/main.py
# 2. Import errors
# 3. Port 8080 already in use

# Fix port conflict:
docker compose down
# Edit docker-compose.yml, change 8080:8080 to 8081:8080
docker compose up -d
```

### Issue: Ollama Model Not Downloaded

**Symptom:**
```bash
curl http://localhost:11434/api/tags
# Returns empty models list
```

**Solution:**
```bash
# Manually pull model
docker exec -it cogniscribe-ollama ollama pull llama3.1:8b

# Watch progress
docker logs -f cogniscribe-ollama
```

### Issue: "Connection Refused" to Ollama

**Symptom:**
API logs show: `Connection refused to http://ollama:11434`

**Solution:**
```bash
# Check Ollama is running
docker compose ps ollama

# Restart services in order
docker compose down
docker compose up -d ollama
sleep 30  # Wait for Ollama
docker compose up -d api
```

### Issue: "ModuleNotFoundError" in API

**Symptom:**
```
ModuleNotFoundError: No module named 'src'
```

**Solution:**
```bash
# Check PYTHONPATH in Dockerfile
# Rebuild without cache
docker compose down
docker compose build --no-cache api
docker compose up -d
```

### Issue: Out of Disk Space

**Symptom:**
```
Error: no space left on device
```

**Solution:**
```bash
# Clean Docker resources
docker system prune -a --volumes

# Remove old images
docker image prune -a

# Check disk usage
docker system df
```

---

## 🛠️ Configuration

### Environment Variables

Edit `docker-compose.yml` to customize:

```yaml
environment:
  # Change Ollama model
  OLLAMA_MODEL: llama3.1:8b  # or llama2:7b, mistral:7b
  
  # Change Whisper model size
  WHISPER_MODEL: base  # tiny, base, small, medium, large
  
  # Enable GPU (requires nvidia-docker)
  USE_GPU: "true"
  
  # Enable PHI detection
  PHI_DETECTION_ENABLED: "true"
  
  # Adjust file size limit (MB)
  MAX_FILE_SIZE_MB: 1000
  
  # Change log level
  LOG_LEVEL: DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### GPU Support (NVIDIA)

1. Install [nvidia-docker](https://github.com/NVIDIA/nvidia-docker)
2. Uncomment GPU section in `docker-compose.yml`:

```yaml
api:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

3. Set environment variable:
```yaml
USE_GPU: "true"
```

---

## 📊 Monitoring

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f ollama

# Last 100 lines
docker compose logs --tail=100 api
```

### Resource Usage
```bash
# Real-time stats
docker stats

# Expected usage:
# API: ~500MB RAM, <5% CPU (idle)
# Ollama: ~2GB RAM, <10% CPU (idle)
# Ollama: ~4GB RAM, 80-100% CPU (processing)
```

### Disk Usage
```bash
# Check volume sizes
docker system df -v

# Ollama models: ~4-10GB
# Audio storage: varies
# Temp processing: <1GB
```

---

## 🔄 Updates

### Update to Latest Version
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d

# Verify
curl http://localhost:8080/api/health
```

### Update Ollama Model
```bash
# Pull new model
docker exec -it cogniscribe-ollama ollama pull llama3.1:latest

# List installed models
docker exec -it cogniscribe-ollama ollama list

# Remove old model
docker exec -it cogniscribe-ollama ollama rm llama3.1:8b
```

---

## 🗑️ Cleanup

### Stop Services
```bash
# Stop but keep data
docker compose down

# Stop and remove volumes (DELETE ALL DATA)
docker compose down -v
```

### Complete Removal
```bash
# Stop everything
docker compose down -v

# Remove images
docker rmi cogniscribe-api:latest
docker rmi ollama/ollama:latest

# Remove network
docker network rm cogniscribe-network
```

---

## 🌐 Production Deployment

### Security Checklist
- [ ] Enable authentication (`COGNISCRIBE_AUTH_ENABLED="true"`)
- [ ] Set strong `JWT_SECRET_KEY`
- [ ] Use HTTPS with reverse proxy (nginx/Caddy)
- [ ] Enable PHI detection (`PHI_DETECTION_ENABLED="true"`)
- [ ] Set up backup for volumes
- [ ] Configure firewall rules
- [ ] Enable audit logging
- [ ] Set up monitoring (Prometheus/Grafana)

### Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name cogniscribe.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for long audio processing
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
    }
}
```

### Backup Strategy
```bash
# Backup volumes
docker run --rm \
  -v cogniscribe_audio_storage:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/audio-$(date +%Y%m%d).tar.gz /data

# Backup Ollama models
docker run --rm \
  -v cogniscribe_ollama_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/ollama-$(date +%Y%m%d).tar.gz /data
```

---

## 📞 Support

If deployment fails:

1. Check logs: `docker compose logs`
2. Verify prerequisites: Docker version, disk space
3. Try rebuild: `docker compose build --no-cache`
4. Open issue: [GitHub Issues](https://github.com/Excelsior2026/COGNISCRIBE/issues)

Include:
- Output of `docker compose logs`
- Output of `docker compose ps`
- Your OS and Docker version
- Steps you've already tried
