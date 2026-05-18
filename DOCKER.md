# Docker Deployment Guide

## สำหรับผู้ใช้งาน

### วิธีเร็วสุด - ใช้ Docker

```bash
# 1. Pull image จาก Docker Hub
docker pull kanoon254569-cell/store:latest

# 2. Run container
docker run -p 8000:8000 kanoon254569-cell/store:latest

# 3. เปิด browser
http://localhost:8000
```

### หรือใช้ Docker Compose

```bash
# Clone repository
git clone https://github.com/kanoon254569-cell/store.git
cd store

# Run with Docker Compose
docker-compose up
```

---

## สำหรับผู้สร้าง - Build & Push

### 1. Build Image
```bash
docker build -t kanoon254569-cell/store:latest .
```

### 2. Tag Image
```bash
docker tag kanoon254569-cell/store:latest kanoon254569-cell/store:1.0
```

### 3. Push to Docker Hub
```bash
# Login first
docker login

# Push
docker push kanoon254569-cell/store:latest
docker push kanoon254569-cell/store:1.0
```

---

## Access

- **Web**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Admin**: admin@ecommerce.local

---

## Environment Variables

ตั้งค่า environment ตามต้องการ:

```bash
docker run -p 8000:8000 \
  -e MONGODB_URL="your_db_url" \
  -e JWT_SECRET="your_secret" \
  kanoon254569-cell/store:latest
```

---

## Stop Container

```bash
docker stop <container_id>
docker rm <container_id>
```
