# IP-SAKTI

IP-SAKTI is a small FastAPI + Vite modular-monolith MVP for the SIH 2026 challenge.

## Local setup

### Backend

From the repository root, create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

Start the API:

```powershell
uvicorn app.main:app --app-dir backend --reload
```

The backend uses Ollama with `qwen3:8b` by default when it is available. It falls back to a deterministic local provider if Ollama is unavailable. Configuration can be overridden with `IP_SAKTI_LLM_PROVIDER`, `IP_SAKTI_OLLAMA_BASE_URL`, `IP_SAKTI_OLLAMA_MODEL`, `IP_SAKTI_OLLAMA_TIMEOUT_SECONDS`, and `IP_SAKTI_RETRIEVAL_LIMIT`.

The API is available at `http://localhost:8000`. Check it with:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

### Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite, usually `http://localhost:5173`.

## Tests and build

From the repository root:

```powershell
pytest -q
cd frontend
npm run build
```

## Current scope

The frontend calls `POST /api/query` and displays the answer, grounded status, provider, confidence, and retrieved evidence. Retrieval uses a deterministic in-memory synthetic knowledge base. Ollama generation is optional and the fallback response is explicitly labelled demo/fallback. The documents and evidence are synthetic and are not legal or regulatory advice. No database, vector database, embeddings, authentication, external API, or authoritative legal/regulatory source has been integrated.
