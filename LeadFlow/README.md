# LeadFlow



A modern web application for managing leads, tracking follow-ups, importing contacts, and automating email notifications.



**Live Demo:** https://lead-flow-eight-zeta.vercel.app/



## Overview



LeadFlow helps users organize and manage their leads through a clean, user-friendly dashboard. It provides tools to import lead data, monitor follow-ups, manage lead information, and automate email notifications.



## Features



- **Dashboard:** View and manage lead information.

- **Lead Management:** Add, update, search, filter, and organize leads.

- **CSV Import:** Import multiple leads using CSV files.

- **Follow-up Tracking:** Track pending, completed, and overdue follow-ups.

- **Email Notifications:** Send automated email notifications using the Resend API.

- **Settings:** Configure application settings and email integration.



## Technology Stack



| Component | Technology |

|---|---|

| Frontend | React, Vite |

| Styling | CSS |

| Backend | Python, FastAPI |

| Database | PostgreSQL (deployed), SQLite (local development) |

| Email Service | Resend API |

| Deployment | Vercel, Render |



## Live Application



Frontend: https://lead-flow-eight-zeta.vercel.app/



Backend API: https://leadflow-api-7i3c.onrender.com



## Run Locally



### 1. Clone the repository



```bash

git clone https://github.com/shreyshah28/LeadFlow.git

cd LeadFlow

```



### 2. Start the backend



```bash

cd backend

python -m venv venv

```



Activate the virtual environment on Windows:



```powershell

.\venv\\Scripts\\Activate.ps1

```



Install dependencies:



```bash

pip install -r requirements.txt

```



Configure the required environment variables using the provided `.env.example` file, then start the backend:



```bash

python main.py

```



### 3. Start the frontend



Open another terminal:



```bash

cd frontend

npm install

npm run dev

```



Open the local URL displayed by Vite in your browser.



## Deployment



- Frontend deployed on Vercel.

- Backend deployed on Render.

- PostgreSQL used for the deployed application.



## AI Tools Used



- ChatGPT

- Antigravity AI



Used for development assistance, debugging, code improvements, and testing.



## Developer



**Shrey Shah**



GitHub: https://github.com/shreyshah28


