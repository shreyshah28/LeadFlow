# LeadFlow — Lead & Follow-up Tracker

**Live Application:** https://lead-flow-eight-zeta.vercel.app/

**Backend API:** https://leadflow-api-7i3c.onrender.com

LeadFlow is a web application designed to simplify lead management, organize prospective clients, track follow-ups, and automate email notifications.

Built using React, FastAPI, and PostgreSQL, LeadFlow provides an intuitive interface for managing leads and monitoring follow-up activities.

## Features

- **Dashboard:** View lead statistics and important business metrics.
- **Lead Management:** Add, edit, search, filter, and manage lead records.
- **Follow-up Tracking:** Monitor pending, completed, overdue, and upcoming follow-ups.
- **CSV Import:** Import multiple leads through a simple file upload interface with validation and error reporting.
- **CSV Export:** Export lead records for external use.
- **Email Notifications:** Automated email notifications using the Resend API.
- **Settings:** Manage application and email configuration.
- **Responsive Interface:** Clean interface designed for convenient lead management.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React 19, Vite 8, JavaScript |
| Styling | CSS3 |
| Backend | Python, FastAPI |
| Database | PostgreSQL (deployed), SQLite (local development) |
| ORM | SQLAlchemy |
| Email Service | Resend API |
| Testing | Python automated tests, Oxlint |
| Deployment | Vercel, Render |

## Project Structure

```text
LeadFlow/
├── .github/
│   └── workflows/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── migrate_db.py
│   ├── email_service.py
│   ├── requirements.txt
│   └── .env.example
├── LeadFlow/
│   └── frontend/
│       ├── public/
│       ├── src/
│       │   ├── components/
│       │   ├── services/
│       │   ├── utils/
│       │   ├── App.jsx
│       │   └── index.css
│       ├── package.json
│       └── .env.example
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10 or later
- Node.js 18 or later
- npm

### 1. Clone the repository

```bash
git clone https://github.com/shreyshah28/LeadFlow.git
cd LeadFlow
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
```

Activate the virtual environment on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the required environment variables using `backend/.env.example`.

Start the backend:

```bash
python main.py
```

Backend URL: http://localhost:8000

API Documentation: http://localhost:8000/docs

### 3. Frontend Setup

Open another terminal from the repository root:

```bash
cd LeadFlow/frontend
npm install
```

Create a `.env` file using the provided `.env.example` if needed.

Start the frontend:

```bash
npm run dev
```

Open the local URL displayed by Vite.

## Deployment

| Service | Platform | URL |
|---|---|---|
| Frontend | Vercel | https://lead-flow-eight-zeta.vercel.app/ |
| Backend | Render | https://leadflow-api-7i3c.onrender.com |

The deployed application uses PostgreSQL for database management.

## AI Tools Used

- ChatGPT
- Antigravity AI

These tools were used for development assistance, debugging, code improvements, and testing.

## Developer

**Shrey Shah**

GitHub: https://github.com/shreyshah28