# BugBuster Changelog

## Latest Update - Semgrep Integration & Bug Fixes (December 2024)

### 🎯 Major Features Added

#### 1. Semgrep Static Code Analysis Tool
- **Added Semgrep Docker Image**: New Dockerfile for Semgrep static analysis tool
  - Location: `docker-tools/semgrep/Dockerfile`
  - Supports buffer overflow detection, SQL injection, command injection, hardcoded secrets, and more
  
- **Backend Integration**:
  - New `SemgrepTool` class in `backend/app/docker/tools.py`
  - Integrated into `ScanService` for localhost testing
  - Supports scanning actual source code directories from host machine
  - Automatic language detection for C#, Python, JavaScript, and more

- **Frontend Integration**:
  - Updated `LocalHostTesting.jsx` page with Semgrep branding
  - Added "Source Code Path" input field for scanning local projects
  - Enhanced UI with loading indicators and progress messages

#### 2. Dashboard Redesign
- Split dashboard into two distinct phases:
  - **Phase 1: Static Code Analysis** - Uses Semgrep for code scanning
  - **Phase 2: Dynamic Analysis Web Penetration Scanner** - Full suite (Sublist3r, Httpx, Gobuster, ZAP, Nuclei, SQLMap)
- Updated `frontend/src/pages/Dashboard.jsx` with new two-button layout

### 🐛 Bug Fixes

#### 1. Target Creation Duplicate Key Error
- **Problem**: New users couldn't create scans with URLs that already existed in database
- **Fix**: Modified `backend/app/api/v1/endpoints/scans.py` to:
  - Check if target exists globally (not per-user) since URL has unique constraint
  - Reuse existing targets if URL already exists
  - Handle race conditions with proper error handling
  - File: `backend/app/api/v1/endpoints/scans.py` (lines 194-223)

#### 2. Frontend Timeout Issues
- **Problem**: Semgrep scans timing out after 3 seconds for large codebases
- **Fix**: Increased API timeout from 3 seconds to 5 minutes (300,000ms)
  - File: `frontend/src/services/api.js` (line 42)
  - Added Semgrep memory and timeout limits in `backend/app/docker/tools.py`

#### 3. Semgrep Configuration Improvements
- Fixed Semgrep command to use `--config=auto --config=p/security-audit` for better C# support
- Removed invalid `p/c-security-critical` config
- Improved error handling for empty JSON outputs
- Enhanced file path handling for Windows host paths

### 📝 Files Modified

1. **backend/app/api/v1/endpoints/scans.py**
   - Fixed target creation logic to handle duplicate URLs
   - Added race condition handling
   - Improved error messages

2. **backend/app/docker/tools.py**
   - Added `SemgrepTool` class implementation
   - Enhanced Semgrep command with timeout and memory limits
   - Improved JSON parsing and error handling
   - Better support for C# project scanning

3. **backend/app/services/scan_service.py**
   - Integrated Semgrep tool into scan workflow
   - Added `execute_localhost_testing` method
   - Registered Semgrep in tools map

4. **frontend/src/pages/LocalHostTesting.jsx**
   - Updated UI to reflect Semgrep as primary tool
   - Added source code path input field
   - Enhanced loading indicators with progress messages
   - Improved error handling and user feedback

5. **frontend/src/pages/Dashboard.jsx**
   - Redesigned with two-phase button layout
   - Phase 1: Static Code Analysis (Semgrep)
   - Phase 2: Dynamic Analysis (Full Suite)

6. **frontend/src/services/api.js**
   - Increased timeout from 3,000ms to 300,000ms (5 minutes)
   - Better support for long-running Semgrep scans

### 🚀 How to Use New Features

#### Running Semgrep Scan:
1. Navigate to Dashboard → "Phase 1: Static Code Analysis"
2. Enter target URL (e.g., `http://localhost:5000`)
3. (Optional) Enter source code path (e.g., `C:\Users\username\Desktop\MyProject`)
4. Click "Run Semgrep Scan"
5. Wait for results (may take 1-3 minutes for large codebases)

#### Building Semgrep Docker Image:
```bash
cd docker-tools/semgrep
docker build -t security-tools:semgrep .
```

### 📦 Dependencies

No new dependencies added. Semgrep is installed inside Docker container.

### 🔧 Configuration

No additional configuration required. All settings are handled automatically.

### ⚠️ Breaking Changes

None. All changes are backward compatible.

### 📚 Documentation

- See `SEMGREP_INTEGRATION.md` for detailed Semgrep setup instructions
- See `SETUP_COMPLETE.md` for general project setup
- See `README_WINDOWS.md` for Windows-specific setup

---

## Previous Updates

### Database Schema Updates
- UUID-based job IDs
- Enhanced vulnerability tracking
- Target management system
- See `DATABASE_UPDATE_SUMMARY.md` for details

### Authentication Fixes
- Login system improvements
- Token handling fixes
- See `LOGIN_FIX_SUMMARY.md` for details

