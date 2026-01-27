# Clarity AI Assistant

A powerful AI assistant for search, document management, and video summaries.

## Features

- AI-powered search with source citations
- YouTube video summarization
- Document management with sharing capabilities
- Modern, responsive UI built with Vite and TailwindCSS

## Setup

### Backend Setup

1. Create a virtual environment and activate it:
```bash
python -m venv env
source env/bin/activate  # On Windows: .\env\Scripts\activate
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

### Running the Application

1. Start the backend server:
```bash
uvicorn clarity_fastapi_app:app --reload
```

2. For production, build the frontend:
```bash
cd frontend
npm run build
```

## Development

- Backend API is built with FastAPI
- Frontend uses Vite + JavaScript
- Styling with TailwindCSS
- Database: SQLite with SQLAlchemy ORM

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
