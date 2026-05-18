---
layout: default
title: Deployment
---

# 🚀 Deployment Guide

Choose your deployment method

---

## Option 1: GitHub Actions + Heroku (Recommended)

### Setup:
1. Create Heroku account (free)
2. Create app: `heroku create your-app-name`
3. Set container stack: `heroku stack:set container`
4. Add GitHub Secrets:
   - `HEROKU_API_KEY`
   - `HEROKU_APP_NAME`
5. Push to main: `git push origin main`

**Time**: ~5-10 minutes  
**Cost**: Free tier available  
**Maintenance**: Zero (auto-deploy)

---

## Option 2: Railway (One-Click Deploy)

### Setup:
1. Go to https://railway.app
2. Login with GitHub
3. Create new project
4. Select this repository
5. Deploy button

**Time**: ~3-5 minutes  
**Cost**: $5/month free credits  
**Maintenance**: Zero (auto-deploy)

---

## Option 3: Docker + Manual Deploy

### Build:
```bash
docker build -t ecommerce:latest .
docker run -p 8000:8000 ecommerce:latest
```

### Push to Docker Hub:
```bash
docker tag ecommerce:latest username/ecommerce:latest
docker push username/ecommerce:latest
```

---

## Environment Variables

Set these in your deployment platform:

```
MONGODB_URL=your_database_url
JWT_SECRET=your_secret_key
ADMIN_EMAIL=admin@ecommerce.local
ENVIRONMENT=production
```

---

## Monitor & Logs

### Heroku:
```bash
heroku logs --tail
heroku apps:info your-app-name
```

### Railway:
- Dashboard → Project → Logs

---

[← Back to Home](/)
