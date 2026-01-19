# Morning Brief AGI - Quick Start Guide

Get your intelligent morning brief running in **5 minutes**! ☀️

## 🚀 Fast Track (Docker)

### 1. Start Everything

```bash
# Clone and enter directory
git clone <repository-url>
cd pal

# Start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up -d

# Initialize database
make db-init

# Check status
docker-compose ps
```

### 2. Access the Application

Open in your browser:
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

You'll see a basic dashboard with stub data. Now let's add real data sources!

## 📧 Enable Real Data (Optional Setup)

### Option A: Google Services (Gmail, Calendar, Tasks)

**Requires:** Google OAuth setup (~15 minutes)

See [MCP_CONNECTOR_SETUP.md](MCP_CONNECTOR_SETUP.md) for detailed instructions.

**Quick version:**
1. Create Google Cloud project
2. Enable Gmail, Calendar, Tasks APIs
3. Create OAuth credentials
4. Download `credentials.json` to `backend/`
5. Run connector for first-time auth

```bash
cd backend
python -c "
from packages.connectors.gmail import GmailConnector
gmail = GmailConnector()
messages = gmail.fetch_messages()
print(f'Found {len(messages)} emails')
"
```

### Option B: LLM for "Why It Matters" (Recommended)

Choose one:

**🆓 Local Ollama (Free, Private)**
```bash
# Install Ollama
brew install ollama  # macOS
# or visit https://ollama.ai for other platforms

# Pull a model
ollama pull llama3.2

# Start server
ollama serve

# Configure in backend/.env
echo "LLM_PROVIDER=ollama" >> backend/.env
echo "LLM_MODEL=llama3.2" >> backend/.env
```

**☁️ Claude API (Best Quality)**
```bash
# Get API key from https://console.anthropic.com

# Configure in backend/.env
echo "LLM_PROVIDER=claude" >> backend/.env
echo "ANTHROPIC_API_KEY=sk-ant-your-key" >> backend/.env
```

**🔄 Test It**
```bash
cd backend
python scripts/test_synthesis.py
```

## 🧪 Generate Your First Brief

### Manual Test

```bash
cd backend
python -c "
import asyncio
from packages.orchestrator import run_brief_generation

async def test():
    brief = await run_brief_generation(
        user_id='u_dev',
        user_preferences={
            'topics': ['AI', 'technology', 'startups'],
            'vip_people': [],
            'projects': []
        },
        modules=['gmail', 'calendar', 'tasks'],
        progress_callback=lambda s, p, m: print(f'{s}: {m}')
    )
    print(f'\nBrief ID: {brief.brief_id}')
    print(f'Status: {brief.status}')
    print(f'Modules: {len(brief.modules)}')
    print(f'Highlights: {len(brief.top_highlights)}')
    
asyncio.run(test())
"
```

### Via API

```bash
# Trigger brief generation
curl -X POST http://localhost:8000/api/brief/run

# Get latest brief
curl http://localhost:8000/api/brief/latest | jq

# View in dashboard
open http://localhost:3000
```

## 🧰 Useful Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart services
docker-compose restart backend
docker-compose restart frontend

# Stop everything
docker-compose down

# Reset database (clean slate)
make reset-db

# View all commands
make help
```

## 🔧 Test Individual Components

### Test Memory System
```bash
cd backend
python scripts/test_memory.py
```

Expected output:
```
✅ Fingerprinting generates stable IDs
✅ Memory manager persists correctly
✅ Novelty detector labels accurately
✅ All tests passed!
```

### Test Ranking
```bash
cd backend
python scripts/test_ranking.py
```

Expected output:
```
✅ Feature extraction working
✅ Ranking scores computed
✅ Top highlights selected
```

### Run the Full Test Suite

```bash
# From project root
cd backend && pytest

# Run with coverage
pytest --cov=packages --cov-report=html
open htmlcov/index.html

# Run specific test categories
pytest tests/test_normalizer.py    # Data transformation
pytest tests/test_ranking.py       # Ranking algorithm
pytest tests/test_memory.py        # Memory/novelty detection
pytest tests/test_database.py      # Database CRUD
pytest tests/test_api.py           # API endpoints
```

**Expected Results:**
- ✅ All 105+ tests should pass
- ✅ Test coverage > 80% for critical modules

See [TESTING.md](./TESTING.md) for comprehensive testing guide.

### Test Individual Components

```bash
cd backend

# Test social agents normalization
python scripts/test_social_agents_simple.py

# Test ranking system
python scripts/test_ranking.py

# Test memory/novelty detection
python scripts/test_memory.py

# Test brief synthesis
python scripts/test_synthesis.py
```

## 💻 Local Development (Without Docker)

### Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (via Docker)
docker run -d \
  --name pal-postgres \
  -e POSTGRES_DB=morning_brief \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:16

# Set up environment
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/morning_brief"

# Initialize database
alembic upgrade head

# Start backend
uvicorn apps.api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set backend URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start frontend
npm run dev
```

## 📊 Configuration Reference

### Environment Variables (backend/.env)

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/morning_brief

# LLM (choose one)
LLM_PROVIDER=ollama  # or "claude" or "openai"
LLM_MODEL=llama3.2
# ANTHROPIC_API_KEY=sk-ant-...  # for Claude
# OPENAI_API_KEY=sk-...         # for OpenAI

# MCP Connectors (optional)
MCP_GMAIL_ENABLED=true
MCP_CALENDAR_ENABLED=true
MCP_TASKS_ENABLED=true

# Social Agents (optional, requires Playwright)
TWITTER_ENABLED=false
LINKEDIN_ENABLED=false
```

### User Preferences

Configure in your user settings or API request:

```python
user_preferences = {
    # Topics you care about (for relevance scoring)
    'topics': [
        'artificial intelligence',
        'startups',
        'machine learning',
        'product management'
    ],
    
    # VIP people whose emails/posts are prioritized
    'vip_people': [
        'ceo@company.com',
        'boss@company.com'
    ],
    
    # Active projects (for context)
    'projects': [
        'product-launch',
        'q4-planning'
    ]
}
```

## 🐛 Troubleshooting

### "Database connection failed"
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart
docker-compose restart postgres
```

### "Port 8000 already in use"
```bash
# Find what's using it
lsof -i :8000

# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### "LLM synthesis failed"
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Or check Claude API key
echo $ANTHROPIC_API_KEY

# Synthesis will fall back to basic summaries if LLM unavailable
```

### "OAuth flow failed"
```bash
# Make sure credentials.json exists
ls backend/credentials.json

# Delete token.json and re-authenticate
rm backend/token.json

# Follow MCP_CONNECTOR_SETUP.md guide
```

### "Frontend shows empty data"
```bash
# Check backend is running
curl http://localhost:8000/api/health

# Trigger a brief generation
curl -X POST http://localhost:8000/api/brief/run

# Check database has data
docker-compose exec postgres psql -U postgres -d morning_brief -c "SELECT COUNT(*) FROM brief_bundles;"
```

## 📚 Next Steps

1. **Run Tests:**
   - `cd backend && pytest` - Verify everything works
   - See [TESTING.md](./TESTING.md) for comprehensive testing guide

2. **Read the docs:**
   - [DEV_LOG.md](../development/DEV_LOG.md) - Understanding how everything works
   - [MCP_CONNECTOR_SETUP.md](./MCP_CONNECTOR_SETUP.md) - Set up Google OAuth
   - [DATABASE_SETUP.md](./DATABASE_SETUP.md) - Database management

3. **Customize your brief:**
   - Configure user preferences
   - Adjust ranking weights
   - Add more data sources

4. **Set up automation:**
   - Schedule daily brief generation (cron job)
   - Add email/SMS notifications
   - Set up monitoring

4. **Extend the system:**
   - Add RSS feeds
   - Integrate more services
   - Build custom modules

## 🎯 What You've Built

You now have a complete system that:

✅ Fetches data from Gmail, Calendar, Tasks (with OAuth)  
✅ Monitors Twitter and LinkedIn (with browser automation)  
✅ Filters out items you've already seen (memory system)  
✅ Ranks everything by importance (5-feature scoring)  
✅ Generates AI explanations (with LLM)  
✅ Packages into a daily brief (orchestrator)  
✅ Displays in a beautiful dashboard (Next.js frontend)

**You're ready to start your day with perfect situational awareness!** ☀️

---

## 🆘 Need Help?

- Check [IMPLEMENTATION_STATUS.md](../development/IMPLEMENTATION_STATUS.md) for current status
- Review [README.md](../../README.md) for complete documentation
- See [docs/architecture/implementation_spec.md](../architecture/implementation_spec.md) for technical details

**Happy briefing!** 📊
