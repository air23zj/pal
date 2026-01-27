# PAL Launch Scripts

Convenient scripts to start and stop the PAL (Morning Brief AGI) application.

## 🚀 Launch Script (`launch.sh`)

Starts the complete PAL application stack:

1. **Checks LM Studio** - Verifies LM Studio is running and accessible
2. **Starts Backend** - Launches the FastAPI server on port 8000
3. **Starts Frontend** - Launches the Next.js dashboard on port 3000
4. **Opens Browser** - Automatically opens Chrome to the dashboard
5. **Tests Integration** - Verifies LLM connectivity

### Usage:
```bash
./scripts/launch.sh
```

### Requirements:
- LM Studio must be running with a model loaded
- Python dependencies installed (`pip install -r backend/requirements.txt`)
- Node.js dependencies installed (`cd frontend && npm install`)

## 🛑 Stop Script (`stop.sh`)

Stops all PAL processes and cleans up:

- Stops backend and frontend servers
- Kills processes by PID or name
- Clears occupied ports
- Removes temporary files

### Usage:
```bash
./scripts/stop.sh
```

## 📊 What the Launch Script Does:

### Pre-flight Checks:
- ✅ LM Studio connectivity test
- ✅ Process cleanup
- ✅ Dependency verification

### Service Startup:
- ✅ Backend server (FastAPI + LLM integration)
- ✅ Frontend server (Next.js dashboard)
- ✅ Health checks for both services
- ✅ LLM integration testing

### User Experience:
- ✅ Automatic browser opening
- ✅ Colored status output
- ✅ Process ID tracking
- ✅ Log file management

## 📁 Generated Files:

When running `launch.sh`, these files are created:
- `logs/backend.log` - Backend server logs
- `logs/frontend.log` - Frontend server logs
- `pids.txt` - Process IDs for easy stopping
- `backend.pid` / `frontend.pid` - Individual process files

## 🔧 Manual Control:

If you prefer manual control, you can also use the Makefile:

```bash
# Start everything
make dev

# Start backend only
make dev-backend

# Start frontend only
make dev-frontend

# Stop everything
make down
```

## 🐛 Troubleshooting:

**"LM Studio is not running"**
- Open LM Studio application
- Load a model (e.g., llama-3.2-3b-instruct)
- Start the local server
- Run `./scripts/launch.sh` again

**"Backend failed to start"**
- Check logs: `tail -f logs/backend.log`
- Ensure dependencies: `cd backend && pip install -r requirements.txt`

**"Frontend failed to start"**
- Check logs: `tail -f logs/frontend.log`
- Ensure dependencies: `cd frontend && npm install`

## 📝 Configuration:

The launch script uses the existing configuration:
- `.env` - Backend environment variables (project root)
- `frontend/.env.local` - Frontend configuration

Make sure LM Studio configuration is set in `.env`:
```
LLM_PROVIDER=openai
OPENAI_BASE_URL=http://localhost:1234/v1
LLM_MODEL=openai/gpt-oss-20b
```