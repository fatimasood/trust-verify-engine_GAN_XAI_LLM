# TrustVerify Engine - Deployment Guide

## Local Deployment

### Prerequisites
- Python 3.10+
- Git
- 8GB RAM minimum
- GPU recommended (NVIDIA CUDA)

### Steps

1. Clone repository
```bash
git clone https://github.com/yourusername/TrustVerify-Engine.git
cd TrustVerify-Engine
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
playwright install
```

4. Configure
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Run Streamlit app
```bash
streamlit run app/streamlit_app.py
```

Access at: http://localhost:8501

## Docker Deployment

### Build Image
```bash
docker build -t trustverify:latest .
```

### Run Container
```bash
docker run -p 8501:8501 -v $(pwd)/data:/app/data trustverify:latest
```

### Docker Compose
```bash
docker-compose up -d
```

## Cloud Deployment

### Heroku Deployment

1. Create Heroku app
```bash
heroku create trustverify-engine
```

2. Add buildpack
```bash
heroku buildpacks:add heroku/python
```

3. Deploy
```bash
git push heroku main
```

### AWS EC2 Deployment

1. Launch EC2 instance (t3.large or larger)
2. SSH into instance
3. Clone repo and follow local deployment steps
4. Use systemd service for auto-restart
5. Configure CloudWatch for monitoring

### Google Cloud Run Deployment

```bash
gcloud run deploy trustverify \
  --source . \
  --platform managed \
  --region us-central1 \
  --port 8501
```

## Production Checklist

- [ ] Set environment variables (.env)
- [ ] Configure database (PostgreSQL)
- [ ] Set up logging
- [ ] Enable HTTPS
- [ ] Configure rate limiting
- [ ] Set up monitoring/alerts
- [ ] Backup strategy for data
- [ ] SSL certificates
- [ ] Security: IP whitelisting
- [ ] Regular model updates