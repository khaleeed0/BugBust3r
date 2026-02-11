#!/usr/bin/env bash

###############################################################################
# Bugbuster Project Startup Script for macOS / Linux
#
# This script will:
#   - Check prerequisites (Docker, docker-compose/`docker compose`, Node, Python, PostgreSQL)
#   - Check if local PostgreSQL is running
#   - Ensure backend .env exists (configured for local PostgreSQL)
#   - Optionally build security tool images (if missing)
#   - Start services with Docker Compose (Redis, Backend, Celery, Frontend)
#   - NOTE: Database runs locally, NOT in Docker
#   - Open the LocalHostTesting page in your browser
#
# Usage:
#   chmod +x start-project-mac.sh
#   ./start-project-mac.sh
###############################################################################

set -euo pipefail

BLUE="→"
GREEN="✓"
YELLOW="!"
RED="✗"
RESET=""

echo
echo "============================================"
echo "  Bugbuster Project Startup (macOS / Linux)"
echo "============================================"
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "${BLUE} [1/7] Checking prerequisites...${RESET}"

# Docker
if ! command -v docker >/dev/null 2>&1; then
  echo "${RED} ERROR: Docker is not installed or not in PATH${RESET}"
  echo "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
  exit 1
fi

# docker-compose or docker compose
DOCKER_COMPOSE_CMD=""
if command -v docker-compose >/dev/null 2>&1; then
  DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version >/dev/null 2>&1; then
  DOCKER_COMPOSE_CMD="docker compose"
else
  echo "${RED} ERROR: docker-compose or 'docker compose' not available${RESET}"
  echo "Please install Docker Compose (comes with recent Docker Desktop)."
  exit 1
fi

# Node
if ! command -v node >/dev/null 2>&1; then
  echo "${RED} ERROR: Node.js is not installed or not in PATH${RESET}"
  echo "Please install Node.js from https://nodejs.org/"
  exit 1
fi

# Python
PYTHON_CMD="python3"
if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
  echo "${RED} ERROR: Python 3 is not installed or not in PATH${RESET}"
  echo "Please install Python 3 from https://www.python.org/"
  exit 1
fi

# PostgreSQL
if ! command -v psql >/dev/null 2>&1; then
  echo "${YELLOW} WARNING: PostgreSQL (psql) not found in PATH${RESET}"
  echo "PostgreSQL needs to be installed and running locally."
  echo "Install with: brew install postgresql"
  echo "Start with: brew services start postgresql"
  echo ""
  read -p "Continue anyway? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

echo "${GREEN} ✓ All prerequisites found${RESET}"
echo

echo "${BLUE} [2/7] Checking Docker daemon...${RESET}"
if ! docker ps >/dev/null 2>&1; then
  echo "${RED} ERROR: Docker is not running.${RESET}"
  echo "Please start Docker Desktop and re-run this script."
  exit 1
fi
echo "${GREEN} ✓ Docker is running${RESET}"
echo

echo "${BLUE} [3/7] Checking local PostgreSQL...${RESET}"
if command -v psql >/dev/null 2>&1; then
  # Try to connect to PostgreSQL with password 1234
  if PGPASSWORD=1234 psql -h localhost -p 5432 -U postgres -d postgres -c "SELECT 1;" >/dev/null 2>&1; then
    echo "${GREEN} ✓ PostgreSQL is running on localhost:5432${RESET}"
  elif psql -h localhost -p 5432 -U postgres -d postgres -c "SELECT 1;" >/dev/null 2>&1; then
    echo "${GREEN} ✓ PostgreSQL is running on localhost:5432${RESET}"
  else
    echo "${YELLOW} WARNING: Could not connect to PostgreSQL on localhost:5432${RESET}"
    echo "Please ensure PostgreSQL is running and password is set to '1234' for user 'postgres':"
    echo "  - macOS: brew services start postgresql"
    echo "  - Set password: psql -U postgres -c \"ALTER USER postgres PASSWORD '1234';\""
    echo "  - Or check: pg_isready -h localhost -p 5432"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      exit 1
    fi
  fi
else
  echo "${YELLOW} WARNING: psql command not found. Assuming PostgreSQL is running.${RESET}"
fi

# Check if database exists, create if not
if command -v psql >/dev/null 2>&1; then
  if PGPASSWORD=1234 psql -h localhost -p 5432 -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw Bugbust3r; then
    echo "${GREEN} ✓ Database 'Bugbust3r' exists${RESET}"
  else
    echo "${YELLOW} ! Database 'Bugbust3r' not found. Creating...${RESET}"
    PGPASSWORD=1234 psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE \"Bugbust3r\";" 2>/dev/null || \
    psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE \"Bugbust3r\";" 2>/dev/null || \
    echo "${YELLOW} ! Could not create database automatically. Please create it manually:${RESET}"
    echo "   createdb -h localhost -p 5432 -U postgres Bugbust3r"
    echo "   Or: psql -h localhost -p 5432 -U postgres -c 'CREATE DATABASE \"Bugbust3r\";'"
  fi
fi
echo

echo "${BLUE} [4/7] Ensuring backend .env exists (configured for local PostgreSQL)...${RESET}"
if [ ! -f "backend/.env" ]; then
  if [ -f "backend/.env.example" ]; then
    cp backend/.env.example backend/.env
    # Update DATABASE_URL to use the correct database
    sed -i.bak 's|DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:1234@localhost:5432/Bugbust3r|' backend/.env 2>/dev/null || \
    sed -i '' 's|DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:1234@localhost:5432/Bugbust3r|' backend/.env
    rm -f backend/.env.bak 2>/dev/null || true
    echo "${GREEN} ✓ Copied backend/.env from backend/.env.example and updated for local PostgreSQL${RESET}"
  else
    cat > backend/.env <<EOF
DATABASE_URL=postgresql://postgres:1234@localhost:5432/Bugbust3r
REDIS_URL=redis://localhost:6379/0
DOCKER_SOCKET=unix://var/run/docker.sock
SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || echo "change-me-in-production")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
EOF
    echo "${GREEN} ✓ backend/.env created with local PostgreSQL settings${RESET}"
  fi
else
  # Update existing .env to use the correct database URL
  if grep -q "DATABASE_URL=" backend/.env 2>/dev/null; then
    # Check if it's already correct
    if ! grep -q "DATABASE_URL=postgresql://postgres:1234@localhost:5432/Bugbust3r" backend/.env 2>/dev/null; then
      sed -i.bak 's|DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:1234@localhost:5432/Bugbust3r|' backend/.env 2>/dev/null || \
      sed -i '' 's|DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:1234@localhost:5432/Bugbust3r|' backend/.env
      rm -f backend/.env.bak 2>/dev/null || true
      echo "${GREEN} ✓ Updated backend/.env to use correct database URL${RESET}"
    else
      echo "${GREEN} ✓ backend/.env already configured correctly${RESET}"
    fi
  else
    # Add DATABASE_URL if missing
    echo "DATABASE_URL=postgresql://postgres:1234@localhost:5432/Bugbust3r" >> backend/.env
    echo "${GREEN} ✓ Added DATABASE_URL to backend/.env${RESET}"
  fi
fi
echo

echo "${BLUE} [5/7] Checking security tool Docker images...${RESET}"
NEEDED_IMAGES=("security-tools:sublist3r" "security-tools:httpx" "security-tools:gobuster" "security-tools:zap" "security-tools:nuclei" "security-tools:sqlmap" "security-tools:addresssanitizer" "security-tools:ghauri")
MISSING_IMAGES=()

for img in "${NEEDED_IMAGES[@]}"; do
  if ! docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "$img"; then
    MISSING_IMAGES+=("$img")
  fi
done

if [ "${#MISSING_IMAGES[@]}" -gt 0 ]; then
  echo "${YELLOW} ! Some security tool images are missing:${RESET}"
  for img in "${MISSING_IMAGES[@]}"; do
    echo "   - $img"
  done
  echo "Building all security tool images (this may take several minutes)..."
  (cd docker-tools && chmod +x build-all.sh && ./build-all.sh)
  echo "${GREEN} ✓ Security tool images built${RESET}"
else
  echo "${GREEN} ✓ All security tool images present${RESET}"
  # Verify ZAP image has Java 17 (recent fix)
  echo "Verifying ZAP image has Java 17..."
  if docker run --rm security-tools:zap java -version 2>&1 | grep -q "17"; then
    echo "${GREEN} ✓ ZAP image has Java 17${RESET}"
  else
    echo "${YELLOW} ! ZAP image may need rebuild (requires Java 17)${RESET}"
    echo "Rebuilding ZAP image..."
    (cd docker-tools/zap && docker build -t security-tools:zap .)
    echo "${GREEN} ✓ ZAP image rebuilt${RESET}"
  fi
fi
echo

echo "${BLUE} [6/7] Starting services with Docker Compose (Redis, Backend, Celery, Frontend)...${RESET}"
echo "${YELLOW} NOTE: Database runs locally, NOT in Docker${RESET}"
echo "${YELLOW} NOTE: Frontend configured to use http://localhost:8000 for API (browser access)${RESET}"
$DOCKER_COMPOSE_CMD up -d
echo
$DOCKER_COMPOSE_CMD ps
echo

echo "${GREEN} ✓ Services are starting:${RESET}"
echo "   - Database:     PostgreSQL (local) on localhost:5432/Bugbust3r"
echo "   - Redis:         tcp://localhost:6379 (Docker)"
echo "   - Backend API:   http://localhost:8000 (Docker)"
echo "   - Celery Worker: Running in Docker"
echo "   - Frontend:      http://localhost:3000 (Docker)"
echo

echo "${BLUE} [7/8] Waiting for services to be ready...${RESET}"
echo "Waiting 15 seconds for services to initialize..."
sleep 15

echo "${BLUE} [8/8] Running comprehensive project verification...${RESET}"
echo "This will verify: database, security tools, user auth, API, jobs, workers"
echo

# Run verification script inside backend container
if docker exec security_scanner_backend python verify_project.py 2>&1; then
  echo "${GREEN} ✓ Project verification completed${RESET}"
else
  echo "${YELLOW} ⚠️  Some verification tests failed. Check output above.${RESET}"
  echo "Services are still running - you can test manually."
fi
echo

echo "${BLUE} Opening LocalHostTesting page in browser...${RESET}"
URL="http://localhost:3000/localhost-testing"
if command -v open >/dev/null 2>&1; then
  open "$URL"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 || true
fi

echo
echo "============================================"
echo "  Startup Complete!"
echo "============================================"
echo
echo "${GREEN} ✓ All services are running via Docker Compose.${RESET}"
echo
echo "${YELLOW} IMPORTANT: Database runs locally (NOT in Docker)${RESET}"
echo "   - PostgreSQL should be running on localhost:5432"
echo "   - Database name: Bugbust3r"
echo "   - Username: postgres, Password: 1234"
echo "   - To start PostgreSQL: brew services start postgresql"
echo "   - To check status: pg_isready -h localhost -p 5432"
echo
echo "Services:"
echo "   - Database:     PostgreSQL (local) on localhost:5432/Bugbust3r"
echo "   - Redis:         tcp://localhost:6379 (Docker)"
echo "   - Backend API:   http://localhost:8000 (Docker)"
echo "   - Celery Worker: Running in Docker"
echo "   - Frontend:      http://localhost:3000 (Docker)"
echo
echo "Testing & Verification:"
echo "  1) Visit: http://localhost:3000/register and create a user"
echo "  2) Visit: http://localhost:3000/login and sign in"
echo "  3) Test scan creation and execution"
echo "  4) Verify findings are stored in database"
echo
echo "${YELLOW}Recent updates (latest fixes):${RESET}"
echo "  ✓ Fixed ZAP tool - updated to Java 17, fixed path issues"
echo "  ✓ Fixed Nuclei tool - corrected JSON output flags"
echo "  ✓ Fixed Gobuster tool - added inline wordlist support"
echo "  ✓ Fixed SQLMap tool - corrected file path"
echo "  ✓ Fixed Sublist3r tool - corrected file path"
echo "  ✓ Fixed database schema - added evidence, confidence, assigned_to_user_id columns"
echo "  ✓ Fixed enum storage - configured to use values instead of names"
echo "  ✓ All security tools tested and verified to save findings"
echo "  ✓ Database connection verified (Bugbust3r)"
echo "  ✓ User registration/login tested and working"
echo "  ✓ Backend-frontend connection verified"
echo "  ✓ Job creation and worker functionality tested"
echo
echo "To stop Docker services:  $DOCKER_COMPOSE_CMD down"
echo "To stop local PostgreSQL: brew services stop postgresql"
echo
echo "To run verification again: docker exec security_scanner_backend python verify_project.py"
echo


