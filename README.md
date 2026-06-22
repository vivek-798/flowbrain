# FlowBrain AI Chief of Staff MVP

FlowBrain is an AI-powered Chief of Staff designed for startup founders. It aggregates operational signals by scanning Gmail, Google Calendar, GitHub, and Notion integrations, analyzes business alerts using LLMs, and presents real-time founder briefings.

This repository contains the complete MVP project structure, frontend routing, database schemas, mock integration endpoints, and beautiful dark SaaS dashboard dashboards.

---

## 📂 Project Structure

```text
flowbrain/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/         # FastAPI Skeletal Routes (auth, briefing, integrations, settings)
│   │   ├── core/               # App configuration, security, database setups
│   │   ├── models/             # SQLAlchemy Database Models (User, Integration, Briefing, Project)
│   │   ├── schemas/            # Pydantic validation schemas
│   │   ├── services/           # Gmail, Calendar, GitHub, Notion, & LiteLLM stubs
│   │   └── main.py             # FastAPI Server Entrypoint
│   ├── .env.example
│   ├── .env                    # Configured locally with SQLite database fallback
│   └── requirements.txt        # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/         # Layout panels (Sidebar, Header)
│   │   ├── pages/              # Styled Dashboards, login pages, integrations configurations
│   │   ├── services/           # Axios API Client service wrappers
│   │   ├── App.tsx             # React Router with Route Guard filters
│   │   └── main.tsx            # React Mount and Query Client Provider
│   ├── package.json
│   ├── tailwind.config.js      # Color tokens matching UI specifications
│   └── vite.config.ts          # Path alias configuration & proxy route mapper
└── README.md
```

---

## ⚡ Getting Started

Ensure the project runs immediately with the following steps.

### 🐍 Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment (optional but recommended):**
   ```bash
   # Windows PowerShell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install python packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the FastAPI server:**
   ```bash
   uvicorn app.main:app --reload
   ```
   *The server starts on `http://localhost:8000`. The API document editor (swagger) is visible at `http://localhost:8000/docs`.*
   *Note: On startup, SQLAlchemy automatically initializes a local database file `flowbrain.db` inside the backend directory.*

---

### 💻 Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd ../frontend
   ```

2. **Install node packages:**
   ```bash
   npm install
   ```

3. **Run the Vite development server:**
   ```bash
   npm run dev
   ```
   *The React web app will run on `http://localhost:5173`. Open your browser and navigate to this address.*

---

## 🔧 Environment Configuration

A default `.env` file is generated inside the `backend/` directory which allows local runs out of the box using SQLite.

To configure PostgreSQL (Supabase) and real external integrations, modify the `.env` settings:
- `DATABASE_URL`: Set to your Supabase/PostgreSQL connection string.
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`: Sourced from the Google Cloud Console for OAuth.
- `ANTHROPIC_API_KEY`: Set to invoke Claude models via LiteLLM.
