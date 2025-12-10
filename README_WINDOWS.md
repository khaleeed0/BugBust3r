# Windows Quick Start Guide

## 🚀 Quick Start

1. **Double-click** `start-project.bat`
2. Wait for all services to start (2-5 minutes on first run)
3. Browser will automatically open to LocalHostTesting page

That's it! 🎉

## 📋 Prerequisites

Before running, ensure you have:

- ✅ **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop)
- ✅ **Node.js** (v16+) - [Download](https://nodejs.org/)
- ✅ **Python** (v3.8+) - [Download](https://www.python.org/)

## 📁 Files

- `start-project.bat` - Start all services
- `stop-project.bat` - Stop all services
- `WINDOWS_STARTUP_GUIDE.md` - Detailed guide

## 🎯 What Gets Started

- ✅ PostgreSQL Database (port 5433)
- ✅ Redis (port 6379)
- ✅ OWASP ZAP Docker Image
- ✅ Backend API (port 8000)
- ✅ Frontend (port 3000)
- ✅ Opens LocalHostTesting page

## 🔧 Troubleshooting

### Docker Not Running
- Start Docker Desktop first
- Wait for whale icon in system tray

### Port Already in Use
- Run `stop-project.bat` first
- Or close existing services manually

### First Time Setup
- First run takes longer (downloads dependencies)
- OWASP ZAP build takes 5-10 minutes
- Be patient! ☕

## 📖 Full Documentation

See `WINDOWS_STARTUP_GUIDE.md` for complete details.

