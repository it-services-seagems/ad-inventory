Quick run instructions

Goal: keep the existing legacy Flask service available for Production and provide an easy way to run the FastAPI-based homologation instance.

Files added:
- `start_flask_prod.ps1` — PowerShell script to start the legacy Flask app under Waitress (production-ready WSGI server on Windows).
- `start_homologacao.ps1` — PowerShell script to start the FastAPI app (uvicorn) for homologation/testing.
- `.env.production.example` — environment variable template for production.
- `.env.homologacao.example` — environment variable template for homologation.

Recommended usage

1) Production (legacy Flask)
- Copy `.env.production.example` to `.env` in `backend` (or set real environment variables in the host/service).
- Activate the virtualenv and run the script from PowerShell (in the `backend` folder):

```powershell
.\start_flask_prod.ps1
```

This runs Waitress hosting the WSGI app defined in `backend/app.py` as `app:app` on port 8000 by default. For production you can hook this into a Windows Service manager, a container, or IIS/ARR as needed.

2) Homologation / Staging (FastAPI)
- Copy `.env.homologacao.example` to `.env.homologacao` (or set env vars) and start the homologation server from `backend`:

```powershell
.\start_homologacao.ps1
```

This runs `uvicorn app.main:app` on `127.0.0.1:8001` with `--reload` enabled for convenience while testing.

## Environment folders and multiple frontends

I added a structured environments folder layout so you can keep separate environment files for backend and frontend per environment.

- `environments/backend/production/.env`  — production backend .env
- `environments/backend/homologacao/.env` — homologation backend .env
- `environments/frontend/production/.env` — production frontend build-time .env
- `environments/frontend/homologacao/.env` — homologation frontend build-time .env

Backend startup scripts (`backend` folder)
- `start_flask_prod.ps1 [Env]` — starts the legacy Flask app under Waitress; optional parameter `Env` selects which env folder to copy from (default `production`). Example:

```powershell
.\start_flask_prod.ps1 production
```

- `start_homologacao.ps1 [Env]` — starts FastAPI homologation; optional parameter `Env` selects which backend env to copy (default `homologacao`). Example:

```powershell
.\start_homologacao.ps1 homologacao
```

Frontend commands (`frontend` folder)
- Development homologation (copies `environments/frontend/homologacao/.env` to `frontend/.env` then runs vite dev server):

```powershell
cd frontend
npm run dev:homologacao
```

- Production build for frontend (copies `environments/frontend/production/.env` then runs the build):

```powershell
cd frontend
npm run build:prod
```

This lets you maintain separate environment configurations for production and homologation and run two independent frontends and backends.

If you want, I can: 
- Add docker-compose to run both environments simultaneously (frontend+backend pairs).
- Add scripts to produce distinct output folders for the two frontends (e.g., `build-homologacao` vs `build-prod`).
- Create lightweight supervisor wrappers to run them as Windows Services.

Notes and next steps
- The legacy Flask entrypoint is `backend/app.py` (it contains `app = Flask(__name__)`), and the FastAPI entrypoint is `backend/app/main.py`.
- If you prefer a different production WSGI server (e.g., Gunicorn) or a Linux-based deployment, adapt the scripts accordingly.
- If you want I can:
  - Add Windows Service wrapper instructions (NSSM or sc.exe) to run the waitress process as a service.
  - Create docker-compose files for local staging and production images.
  - Wire separate `.env` names into the FastAPI startup so the app can auto-detect APP_ENV.

Tell me which of the next steps you want me to implement and I will do it.