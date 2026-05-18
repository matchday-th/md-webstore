---
layout: default
title: Home
---

# 🛍️ Ecommerce Multi-Vendor System

**High-Performance, Secure E-Commerce Platform**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## ✨ Features

### 📊 Admin Dashboard
- Real-time sales analytics
- Inventory management
- Revenue tracking
- Order monitoring

### 🛒 User Store
- Browse products
- Secure checkout
- Order tracking
- Push notifications

### 👥 Provider Panel
- Product management
- Stock updates
- Sales analytics
- Custom dashboard

### 🔐 Security
- Duplicate purchase prevention
- Rate limiting (DDoS protection)
- Stock validation
- Idempotency key support
- JWT authentication

---

## 🚀 Quick Start

### Option 1: GitHub Actions (Auto Deploy)

1. Fork repository
2. Add Heroku secrets to GitHub
3. Push to `main` → Auto deploy! ✅

### Option 2: Railway (1-Click)

1. https://railway.app
2. Deploy from GitHub repo
3. Get live URL instantly

### Option 3: Local Development

```bash
git clone https://github.com/kanoon254569-cell/store.git
cd store
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

---

## 📱 Access Points

| Component | URL |
|-----------|-----|
| Admin Dashboard | `/` |
| API Documentation | `/docs` |
| Provider Panel | `/provider` |
| User Store | `/store` |

---

## 🔧 Tech Stack

- **Backend**: FastAPI (Python 3.10)
- **Database**: MongoDB / SQLite
- **Frontend**: HTML5 + JavaScript
- **Deployment**: Docker, Heroku, Railway
- **Security**: JWT, bcrypt, rate limiting

---

## 📚 Documentation

- [Deployment Guide](../DEPLOYMENT.md)
- [GitHub Actions Setup](../GITHUB_ACTIONS_DEPLOY.md)
- [Railway Deployment](../RAILWAY_DEPLOY.md)
- [API Documentation](./api.md)

---

## 🔑 Default Admin Credentials

- **Email**: `admin@ecommerce.local`
- **Password**: (Set during installation)

---

## 📊 Project Statistics

- **Endpoints**: 50+
- **Database Models**: 8
- **Security Layers**: 5
- **Test Coverage**: ~80%

---

## 🎯 Next Steps

1. **Deploy** → Choose your platform
2. **Configure** → Set environment variables
3. **Customize** → Add your branding
4. **Monitor** → Track analytics in dashboard

---

## 🤝 Contributing

Pull requests welcome! Please:
1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open pull request

---

## 📞 Support

- 📖 [Full Documentation](./index.md)
- 💬 GitHub Issues
- 📧 Contact admin@ecommerce.local

---

**Made with ❤️ by Your Team**

⭐ Star us on [GitHub](https://github.com/kanoon254569-cell/store)
