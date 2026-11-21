# LeadFlow — Lead & Follow-up Tracker

LeadFlow is a modern, high-performance SaaS Lead Management and Follow-up Tracker designed to streamline sales pipelines, monitor active deals, track follow-up schedules, and organize prospective client relationships.

Built with a **React + Vite** frontend and a **Python + FastAPI + SQLAlchemy** backend, LeadFlow combines a responsive UI with an isolated, transactional database architecture.

---

## 🌟 Key Features

- **Dynamic Sales Dashboard**: Real-time overview cards displaying Total Leads, Contacted, Meetings, Won Leads, Pipeline Deal Value, and Win Rate.
- **Lead Lifecycle Management**: Add new leads, view full details, update statuses, edit contact info, and archive or delete leads.
- **Urgency-Driven Follow-up System**: Automated categorization into **Overdue**, **Due Today**, and **Upcoming** follow-ups calculated dynamically against the current date.
- **Case-Insensitive Search & Filtering**: Multi-field search across company name, contact person, email, and city, with case-normalized city filters and urgency pills.
- **Interactive Multi-Column Sorting**: Sort leads by follow-up date, company name, contact person, deal value, or status.
- **Robust CSV Import & Export**:
  - **Export**: One-click download of leads as Excel-compatible CSV (prefixed with UTF-8 BOM).
  - **Import**: Drag-and-drop CSV importer with instant client-side preview, column mapping validation, row-by-row error reporting, and safe transaction rollbacks.
- **Dual Theme Support (Light & Dark Mode)**:
  - High-contrast, polished modern SaaS dark theme.
  - Quick toggle button in the header and visual selector in Settings.
  - Keyboard shortcut: `Ctrl + D` (or `Cmd + D`).
  - Persistent storage in `localStorage` with zero-flash rendering on page load.
- **Refined SaaS Typography**: Clean, accessible typography powered by Google Fonts' **Manrope** primary family.
- **Production-Ready Database**: SQLite local storage with Write-Ahead Logging (WAL) enabled, accompanied by automatic PostgreSQL readiness via `DATABASE_URL`.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 19, Vite 8, Lucide React icons, CSS3 Custom Properties (Design Tokens) |
| **Backend** | Python 3.10+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Uvicorn |
| **Database** | SQLite 3 (local development with WAL mode), PostgreSQL 15+ (production ready) |
| **Testing & Quality** | Oxlint, Starlette TestClient, HTTPX, Automated Isolated Test Suites |

---

## 📂 Project Structure

```text
LeadFlow/
├── backend/
│   ├── database.py             # Database engine, WAL configuration & connection pooling
│   ├── main.py                 # FastAPI application, REST endpoints & middleware
│   ├── migrate_db.py           # Idempotent schema migration runner
│   ├── models.py               # SQLAlchemy ORM database models
│   ├── requirements.txt        # Python backend dependencies
│   ├── schemas.py              # Pydantic v2 validation models & serializers
│   ├── test_backend.py         # Backend smoke test script
│   ├── test_suite.py           # Comprehensive 51-point automated QA test suite
│   └── .env.example            # Backend environment variables template
├── LeadFlow/
│   └── frontend/
│       ├── public/             # Static assets (favicons, icons)
│       ├── src/
│       │   ├── assets/         # Images and SVG icons
│       │   ├── components/     # React modular components (Table, Modals, Stats, Sidebar)
│       │   ├── data/           # Default seed and sample datasets
│       │   ├── services/       # REST API service client
│       │   ├── utils/          # Date normalization, calculations, and CSV export
│       │   ├── App.jsx         # Main application coordinator
│       │   ├── index.css       # SaaS design tokens, responsive layout & theme rules
│       │   └── main.jsx        # React application entry point
│       ├── index.html          # HTML entry point with anti-flash script & Manrope font
│       ├── package.json        # Frontend dependencies & scripts
│       ├── vite.config.js      # Vite build configuration
│       └── .env.example        # Frontend environment variables template
├── .gitignore                  # Git exclusion rules for databases, venv, and build artifacts
├── package.json                # Root package coordinator scripts
└── README.md                   # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed on your machine:
- **Python**: Version 3.10 or higher
- **Node.js**: Version 18.0 or higher
- **npm** or **pnpm**

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/leadflow.git
cd leadflow
```

---

### Step 2: Backend Setup & Installation

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   - **On Windows**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - **On macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. *(Optional)* Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   *(By default, LeadFlow uses local SQLite `leadflow.db`. No configuration is required for local development.)*

5. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   The backend API will be available at: `http://localhost:8000`
   Interactive Swagger documentation: `http://localhost:8000/docs`

---

### Step 3: Frontend Setup & Installation

Open a new terminal window:

1. Navigate to the frontend directory:
   ```bash
   cd LeadFlow/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. *(Optional)* Set frontend environment variables:
   ```bash
   cp .env.example .env
   ```
   *(Defaults to `VITE_API_URL=http://localhost:8000/api`)*

4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open your browser at: `http://localhost:5173`

---

## ⚙️ Environment Variables

### Backend (`backend/.env`)

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite:///./leadflow.db` | Database connection URL. Accepts SQLite or PostgreSQL (`postgresql://...`). |
| `ENV` | `development` | Setting to `production` disables destructive sample-reset endpoints. |
| `PORT` | `8000` | Port for the Uvicorn server. |

### Frontend (`LeadFlow/frontend/.env`)

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `VITE_API_URL` | `http://localhost:8000/api` | Base URL pointing to the FastAPI backend API. |

---

## 📡 REST API Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status and timestamp. |
| `GET` | `/api/stats` | Aggregated dashboard metrics, status breakdown, and urgent counts. |
| `GET` | `/api/leads` | List leads with optional search, status, city, urgency, and sorting. |
| `GET` | `/api/leads/{id}` | Retrieve details for a specific lead by ID. |
| `POST` | `/api/leads` | Create a new lead record with schema validation. |
| `PUT` | `/api/leads/{id}` | Update existing lead details, status, or follow-up schedule. |
| `DELETE` | `/api/leads/{id}` | Permanently delete a lead record. |
| `POST` | `/api/leads/upload-csv` | Import leads from CSV spreadsheet with transaction safety. |
| `POST` | `/api/leads/reset-sample` | Re-seed sample CRM leads (restricted in production). |

---

## 🧪 Testing & Verification

LeadFlow includes comprehensive test suites running against isolated temporary databases:

### Backend Automated Test Suite (51 Tests)
```bash
cd backend
python test_suite.py
```
*Tests schema constraints, CRUD operations, city normalization, negative deal values, timestamp integrity, sorting parameters, and CSV transaction rollbacks.*

### Backend Smoke Tests
```bash
cd backend
python test_backend.py
```

### Frontend Static Code Analysis (Linter)
```bash
cd LeadFlow/frontend
npm run lint
```

### Frontend Production Build
```bash
cd LeadFlow/frontend
npm run build
```

---

## 📸 Screenshots

### Light Mode Dashboard
*Placeholder: Add screenshot of the active Light Theme dashboard and lead table.*

### Dark Mode Dashboard
*Placeholder: Add screenshot of the Dark Theme dashboard (`Ctrl + D`).*

### CSV Import & Preview Modal
*Placeholder: Add screenshot of the CSV dropzone with client-side preview table.*

---

## 🛡️ Database & Deployment Notes

- **Local Storage**: Uses SQLite with Write-Ahead Logging (`WAL`) mode enabled, ensuring smooth concurrent read/write operations without database lock errors.
- **PostgreSQL Production Deployment**: LeadFlow includes native PostgreSQL compatibility with connection pooling (`psycopg2-binary`). When deploying to platforms like **Render**, **Railway**, **Fly.io**, or **Neon**, simply provide the `DATABASE_URL` environment variable:
  ```bash
  DATABASE_URL=postgresql://user:password@hostname:5432/leadflow
  ```
- **Git Cleanliness**: All local `.db` files, SQLite journal files (`*-wal`, `*-shm`), virtual environments (`venv/`), build outputs (`dist/`), and `.env` credentials are systematically excluded from version control via `.gitignore`.

---

## 🔮 Future Improvements

- [ ] User authentication with JWT and multi-tenant organization workspaces.
- [ ] Email integration to send follow-up reminders directly via SMTP or SendGrid.
- [ ] Activity timeline logs for lead interaction history (calls, emails, notes).
- [ ] Automated webhook triggers for external CRM synchronization (Zapier, Slack).

---

## 📄 License

This project was developed as part of a Web Portal & Payments practical assignment. Distributed under the MIT License.

