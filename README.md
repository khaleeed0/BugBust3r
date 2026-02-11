# Security Scanner - On-Demand Docker-Based Security Scanning Platform

A comprehensive security scanning platform that orchestrates multiple security tools using Docker containers. The platform uses FastAPI for the backend, React for the frontend, and Docker SDK to execute security tools on-demand.

## Features

- **Multi-Stage Security Scanning**: Orchestrates multiple security tools in sequence
- **LocalHost Testing**: AddressSanitizer (C/C++ memory safety) + Ghauri (SQL injection) for localhost targets
- **On-Demand Container Execution**: Uses Docker SDK to run containers when needed
- **User Authentication**: JWT-based authentication system
- **Async Job Processing**: Redis + Celery for background job processing
- **Real-time Status Tracking**: Track scan progress and results
- **Comprehensive Reports**: Detailed reports for each scan job

## Security Tools

**Full scan pipeline:** Sublist3r → Httpx → Gobuster → OWASP ZAP → Nuclei → SQLMap  
**LocalHost Testing (localhost/127.0.0.1 only):** AddressSanitizer → Ghauri

1. **Stage 1 - Subdomain Enumeration**: Sublist3r
2. **Stage 2 - HTTP Service Detection**: Httpx
3. **Stage 3 - Directory Discovery**: Gobuster
4. **Stage 4 - Web Application Scanning**: OWASP ZAP
5. **Stage 5 - Template-Based Scanning**: Nuclei
6. **Stage 6 - SQL Injection Testing**: SQLMap
7. **AddressSanitizer**: C/C++ memory safety (buffer overflow, use-after-free) – used in LocalHost Testing
8. **Ghauri**: SQL injection detection/exploitation (blind SQLi, PostgreSQL-friendly) – used in LocalHost Testing

## Technology Stack

- **Backend**: Python, FastAPI, SQLAlchemy, Celery
- **Frontend**: React.js, Tailwind CSS, Vite
- **Database**: PostgreSQL
- **Message Broker**: Redis
- **Containerization**: Docker, Docker Compose
- **Security Tools**: Sublist3r, Httpx, Gobuster, OWASP ZAP, Nuclei, SQLMap, AddressSanitizer, Ghauri

## Project Structure

```
.
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Configuration and security
│   │   ├── db/          # Database configuration
│   │   ├── docker/      # Docker SDK integration
│   │   ├── models/      # Database models
│   │   └── services/    # Business logic
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # Reusable components
│   │   ├── contexts/    # React contexts
│   │   ├── pages/       # Page components
│   │   └── services/    # API services
│   ├── Dockerfile
│   └── package.json
├── docker-tools/        # Dockerfiles for security tools
│   ├── sublist3r/
│   ├── httpx/
│   ├── gobuster/
│   ├── zap/
│   ├── nuclei/
│   ├── sqlmap/
│   ├── addresssanitizer/
│   └── ghauri/
└── docker-compose.yml   # Orchestration file
```

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)

## Setup Instructions

### 1. Build Security Tool Docker Images

First, build all the security tool Docker images:

```bash
cd docker-tools
chmod +x build-all.sh
./build-all.sh
```

Or build individually:

```bash
cd docker-tools/sublist3r && docker build -t security-tools:sublist3r .
cd docker-tools/httpx && docker build -t security-tools:httpx .
cd docker-tools/gobuster && docker build -t security-tools:gobuster .
cd docker-tools/zap && docker build -t security-tools:zap .
cd docker-tools/nuclei && docker build -t security-tools:nuclei .
cd docker-tools/sqlmap && docker build -t security-tools:sqlmap .
cd docker-tools/addresssanitizer && docker build -t security-tools:addresssanitizer .
cd docker-tools/ghauri && docker build -t security-tools:ghauri .
```

### 2. Environment Configuration

Copy the example environment file:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your configuration (if needed).

### 3. Start Services with Docker Compose

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- Redis
- FastAPI backend
- Celery worker
- React frontend

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 5. Create Initial User

Register a new user through the frontend at http://localhost:3000/register

## Development Setup

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start database and Redis
docker-compose up -d db redis

# Run migrations (tables are created automatically)
# Run the backend
uvicorn app.main:app --reload

# Run Celery worker
celery -A app.services.task_queue.celery_app worker --loglevel=info
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get token
- `GET /api/v1/auth/me` - Get current user info

### Scans
- `POST /api/v1/scans` - Create new scan job
- `GET /api/v1/scans` - Get all scans for current user
- `GET /api/v1/scans/{id}` - Get specific scan

### Jobs
- `GET /api/v1/jobs/{id}/status` - Get job status and results

### Reports
- `GET /api/v1/reports` - Get all reports
- `GET /api/v1/reports/{id}` - Get full report for a job

## Usage

1. **Register/Login**: Create an account or login
2. **Start Scan**: Go to Dashboard and enter a target URL
3. **LocalHost Testing**: Use the LocalHost Testing page for localhost/127.0.0.1 targets – runs AddressSanitizer (optional C/C++ source path) and Ghauri (SQL injection)
4. **Monitor Progress**: Check the Scans page for status
5. **View Reports**: Once completed, view detailed reports

## Notes

- The backend requires Docker socket access to run containers
- Make sure Docker is running before starting scans
- Security tool images must be built before running scans
- Large scans may take significant time to complete

## Security Considerations

- Change the SECRET_KEY in production
- Use environment variables for sensitive data
- Implement rate limiting for production
- Use HTTPS in production
- Regularly update security tool images

## Troubleshooting

### Docker Connection Issues
If you see Docker connection errors, ensure:
- Docker daemon is running
- Docker socket is accessible
- User has Docker permissions

### Database Connection Errors
Check that PostgreSQL is running and credentials are correct in `.env`

### Celery Worker Not Processing Jobs
Ensure Redis is running and worker can connect to it

## License

This project is for educational purposes. Use responsibly and only on systems you own or have permission to test.


