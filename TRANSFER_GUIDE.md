# REAL ESTATE AI ASSISTANT - PROJECT TRANSFER CHECKLIST

## PROJECT LOCATION
**Full Path:** `/Users/jqv0003/Desktop/real_estate_ai_assistant_v2`
**Total Size:** 405 MB (131MB backend + 273MB frontend)

---

## WHAT TO TRANSFER

### Copy This Entire Folder:
```
real_estate_ai_assistant_v2/
```

This contains EVERYTHING you need:
- Backend (FastAPI + Python)
- Frontend (Next.js + React)
- Database (SQLite)
- Configuration files
- All dependencies listed (node_modules and venv will be recreated)

---

## FILES TO CHECK BEFORE TRANSFER

### 1. Backend Environment Variables
**File:** `backend/.env`
**Contains:**
- RentCast API Key: stored locally; do not commit
- RapidAPI Key: stored locally; do not commit
- Google Gemini Key: stored locally; do not commit
- Cache settings

**STATUS:**  Present and configured

### 2. Frontend Environment
**File:** `frontend/.env.local` (if exists)
**Should contain:** API endpoint to backend

### 3. Database
**Location:** `backend/real_estate.db` or `backend/app/real_estate.db`
**Contains:** Cached property data, API responses

---

## CURRENT CONFIGURATION

### Backend Settings (backend/app/core/config.py):
- Demo Mode: OFF (using real APIs)
- RapidAPI: ENABLED
- Multi-source fallback: Zillow Live Data → Real Estate Zillow → Realtor16 → RentCast

### API Status:
-  RentCast: WORKING (limited data)
-  Zillow Live Data: CONFIGURED (needs DNS fix on new machine)
-  Real Estate Zillow: CONFIGURED
-  Realtor16: CONFIGURED
-  Google Gemini: CONFIGURED

### Smart Fallbacks Enabled:
- Tax calculations (1.5% of property value)
- Nearby value estimates
- School lookup by ZIP
- Property type defaults

---

## HOW TO TRANSFER

### Method 1: Compress and Copy (RECOMMENDED)
```bash
cd ~/Desktop
zip -r real_estate_ai_assistant_v2.zip real_estate_ai_assistant_v2 -x "*/node_modules/*" -x "*/.venv/*" -x "*/__pycache__/*"
```

**Result:** Much smaller file (~10-20MB) - excludes large dependency folders

**Then on new machine:**
```bash
unzip real_estate_ai_assistant_v2.zip
cd real_estate_ai_assistant_v2
```

### Method 2: Cloud Storage (Google Drive, OneDrive, Dropbox)
1. Compress using Method 1
2. Upload .zip file
3. Download on other machine
4. Unzip

### Method 3: GitHub (Best for version control)
```bash
cd ~/Desktop/real_estate_ai_assistant_v2
git init
git add .
git commit -m "Initial commit"
# Create repo on GitHub
git remote add origin YOUR_GITHUB_URL
git push -u origin main
```

### Method 4: Copy Full Folder (Slowest)
- Just drag the folder to USB drive or cloud storage
- 405MB transfer

---

## SETUP ON NEW MACHINE

### 1. Install Prerequisites
```bash
# Python 3.11+
python3 --version

# Node.js 18+
node --version

# UV (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Backend Setup
```bash
cd real_estate_ai_assistant_v2/backend

# Create virtual environment
uv venv

# Activate it
source .venv/bin/activate  # Mac/Linux
# OR
.venv\Scripts\activate  # Windows

# Install dependencies
uv pip install -r requirements.txt

# Verify .env exists
cat .env
```

### 3. Frontend Setup
```bash
cd ../frontend

# Install dependencies
npm install

# Create .env.local if needed
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

### 4. DNS Fix (If RapidAPI dn't work)
```bash
# Add Zillow API IP to /etc/hosts
echo '98.91.65.145 zillow-com-live-data-scraper-api.p.rapidapi.com' | sudo tee -a /etc/hosts
```

### 5. Start Everything
```bash
# Terminal 1 - Backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 6. Open Browser
```
http://localhost:3001
```

---

## IMPORTANT FILES TO BACKUP

### Critical (MUST have):
- `backend/.env` - All API keys
- `backend/real_estate.db` - Cached data
- `backend/app/` - All Python code
- `frontend/src/` - All React code
- `frontend/package.json` - Dependencies

### Nice to Have:
- `README.md` - Project documentation
- `SETUP_GUIDE.md` - Setup instructions
- `PROJECT_CHANGES.md` - Change log

---

## WHAT GETS RECREATED (Don't need to transfer):
- `backend/.venv/` - Virtual environment (recreate with `uv venv`)
- `frontend/node_modules/` - Dependencies (recreate with `npm install`)
- `backend/__pycache__/` - Python cache
- `.next/` - Next.js build cache

---

## TESTING AFTER TRANSFER

### 1. Backend Health Check
```bash
curl http://localhost:8000/health
```
**Should return:** `{"status":"healthy"}`

### 2. Test Property Search
Search for: `4141 Peridot Dr, Virginia Beach, VA 23456`

**Should see:**
- Bedrooms, Bathrooms, Sqft, Price
- Tax info (calculated or from API)
- Nearby values
- Schools

### 3. Check Terminal for API Success
```
SUCCESS: Got data from Zillow Live Data
```
OR
```
SUCCESS: Got data from RentCast
```

---

## TROUBLESHOOTING ON NEW MACHINE

### RapidAPI Not Working?
1. Check DNS: `python3 -c "import socket; print(socket.gethostbyname('zillow-com-live-data-scraper-api.p.rapidapi.com'))"`
2. Add to /etc/hosts if needed
3. Flush DNS: `sudo dscacheutil -flushcache`

### Database Errors?
```bash
cd backend
rm real_estate.db
python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"
```

### Port Already in Use?
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --port 8001
```

---

## API KEYS BACKUP (Save Separately!)

**RentCast:** stored locally; do not commit
**RapidAPI:** stored locally; do not commit
**Google Gemini:** stored locally; do not commit

Keep these in a password manager or secure note!

---

## PROJECT STATUS:  READY TO TRANSFER

**Everything is configured and working!**
**Just copy the folder and follow the setup steps on the new machine.**

---

## Questions?

1. **Will my cached data transfer?** Yes, if you include the .db file
2. **Do I need to recreate the venv?** Yes, run `uv venv` on new machine
3. **Will my API keys work?** Yes, they're in the .env file
4. **Can I use this on Windows?** Yes, but use Windows commands for venv activation

**YOU'RE READY TO GO!**
