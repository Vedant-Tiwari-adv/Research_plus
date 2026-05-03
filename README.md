# ⬡ Research+ : Semantic Research Intelligence Platform

A full-stack academic intelligence platform demonstrating semantic search, ML classification, publishability scoring, experiment tracking, real-time monitoring, and JWT authentication — all containerized with Docker.



backend: uvicorn main:app --reload --port 8000
set DATA_PATH=../data/papers.csv
set MLFLOW_TRACKING_URI=../mlruns
set JWT_SECRET=research_plus_super_secret_key_2024
uvicorn main:app --reload --port 8000




grafana run docker: docker-compose up prometheus grafana
ml flow : python -c "from mlflow.cli import cli; cli()" ui --backend-store-uri ./mlruns --port 5000



cd frontend
npm install
set REACT_APP_API_URL=http://localhost:8000
npm start



---

## System Architecture

```
┌──────────────┐    ┌──────────────────────────────────────────┐
│   Browser    │    │               Docker Network              │
│              │◄──►│  React (3000) ──► FastAPI (8000)         │
│  localhost   │    │                      │                    │
│              │◄──►│  Grafana (3001) ◄── Prometheus (9090)    │
│              │◄──►│  MLflow (5000)                           │
└──────────────┘    └──────────────────────────────────────────┘
```

### Component Breakdown

| Component | Technology | Role |
|-----------|-----------|------|
| Backend | FastAPI + Python | REST API, ML inference, auth |
| Frontend | React 18 | Single-page application |
| Embeddings | sentence-transformers (MiniLM-L6) | Semantic search vectors |
| Vector DB | FAISS | ANN similarity search |
| Classifier | TF-IDF + Logistic Regression | Paper categorization |
| Publishability | Linear/Ridge Regression | Score prediction (0–1) |
| ML Tracking | MLflow | Experiment runs & metrics |
| Metrics | Prometheus | Metric collection & scraping |
| Monitoring | Grafana | Real-time dashboards |
| Auth | JWT (python-jose + bcrypt) | Secure route protection |

---

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose v2
- 4GB RAM recommended (sentence-transformers model is ~90MB)

### 1. Clone / Extract

```bash
unzip research_plus.zip
cd research_plus
```

### 2. Start Everything

```bash
docker-compose up --build
```

The first build downloads the MiniLM embedding model (~90MB). Subsequent starts are fast.

Wait for this log line from the backend:

```
=== Research+ ready ===
```

---

## Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | admin / admin123 |
| **API Docs** | http://localhost:8000/docs | — |
| **MLflow UI** | http://localhost:5000 | — |
| **Grafana** | http://localhost:3001 | admin / admin123 |
| **Prometheus** | http://localhost:9090 | — |

---

## Demo Walkthrough

### Step 1 — Login
Open http://localhost:3000, log in with `admin / admin123`.

### Step 2 — Semantic Search
Go to **Search** tab. Try queries like:
- `attention mechanism transformer`
- `image classification convolutional`
- `distributed consensus algorithms`

Results show similarity scores, category badges, and publishability scores.

### Step 3 — Papers Corpus
Browse all 60 papers. Filter by category.

### Step 4 — ML Score
Go to **ML Score** tab. Enter a title, abstract, and metadata. Click **Predict Score** to get a publishability prediction (0–100%).

### Step 5 — Analytics
View **Analytics** tab for bibliometric breakdowns — papers per category, per year, top cited papers.

### Step 6 — Evaluate (Precision@K)
Go to **Evaluate** tab. Run Precision@K to measure how well semantic search retrieves the right category.

### Step 7 — Grafana Monitoring
Open http://localhost:3001 (admin / admin123). Navigate to **Research+ System Dashboard** to see:
- Request rate (per second)
- Latency percentiles (p50 / p95 / p99)
- Error rate
- Login & register activity

### Step 8 — MLflow Experiments
Open http://localhost:5000. Navigate to **Research+ Publishability** experiment.  
You will see **3 runs**:
- `LinearRegression_all_features`
- `Ridge_alpha0.1`
- `Ridge_alpha1.0`

Each run logs: `mse`, `r2`, `rmse`, model parameters, and the trained sklearn model as an artifact.

---

## API Reference

All core endpoints require `Authorization: Bearer <token>` header.

### Auth

```
POST /register
Body: { "username": "...", "password": "...", "email": "..." }

POST /login
Body: { "username": "...", "password": "..." }
Returns: { "access_token": "...", "token_type": "bearer" }
```

### Search

```
GET /search?q=<query>&top_k=10
Returns: { count, latency_ms, results: [...] }
```

### Papers

```
GET /papers?page=1&page_size=20&category=NLP
GET /papers/{id}
```

### ML

```
POST /classify?title=...&abstract=...
POST /publishability?title=...&abstract=...&citations=0&year=2024&keywords=5&category=NLP
```

### Analytics

```
GET /stats
GET /evaluate/precision?q=...&category=...&k=5
```

### Metrics

```
GET /metrics   ← Prometheus scrape endpoint
```

---

## ML Details

### Publishability Score Model

**Features:**
1. `abstract_length` — character count of abstract
2. `keyword_count` — number of keywords
3. `citation_count` — log-normalized citation count
4. `year_normalized` — year scaled to [0, 1]
5. `category_encoded` — label-encoded paper category

**Training:** 3 MLflow runs compare `LinearRegression`, `Ridge(α=0.1)`, `Ridge(α=1.0)`. Best model (lowest MSE) is selected automatically.

**Score interpretation:**
- ≥ 70% → High publishability
- 40–70% → Medium publishability  
- < 40% → Low publishability

### Classifier

TF-IDF (bigrams, 5000 features) + Logistic Regression trained on title + abstract. Categories: Machine Learning, NLP, Computer Vision, Systems, Theory.

### Semantic Search

`all-MiniLM-L6-v2` (384-dim) → FAISS `IndexFlatIP` (inner product on normalized vectors = cosine similarity). In-memory LRU cache (500 entries max).

---

## Project Structure

```
research_plus/
├── backend/
│   ├── main.py            ← FastAPI app, routes, middleware
│   ├── auth.py            ← JWT auth (register/login/protect)
│   ├── search.py          ← FAISS + sentence-transformers + cache
│   ├── classifier.py      ← TF-IDF + Logistic Regression
│   ├── publishability.py  ← Regression model + MLflow tracking
│   ├── metrics.py         ← Prometheus counters & histograms
│   ├── logger.py          ← Rotating file + console logger
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js         ← Full React SPA (Search, Papers, ML, Stats, Eval)
│   │   ├── App.css        ← Dark editorial design system
│   │   └── index.js
│   ├── public/index.html
│   ├── package.json
│   └── nginx.conf
├── monitoring/
│   ├── prometheus.yml     ← Scrape config
│   └── grafana/
│       ├── datasources/prometheus.yml
│       └── dashboards/research_plus.json  ← Pre-built dashboard
├── data/
│   ├── papers.csv         ← 60 synthetic research papers
│   └── generate_dataset.py
├── logs/                  ← Runtime logs (auto-created)
├── mlruns/                ← MLflow artifact store (auto-created)
├── Dockerfile             ← Backend image
├── Dockerfile.frontend    ← React build + Nginx
├── docker-compose.yml     ← Full stack orchestration
└── README.md
```

---

## Stopping

```bash
docker-compose down          # Stop containers
docker-compose down -v       # Stop and remove volumes (resets Grafana)
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Backend slow to start | First run downloads ML model (~90MB). Wait for "ready" log. |
| Grafana shows no data | Make sure Prometheus is scraping: visit http://localhost:9090/targets |
| MLflow shows no runs | Backend must fully start. Runs are logged on startup. |
| CORS errors in browser | Ensure you access via `localhost`, not `127.0.0.1` |
| Port already in use | Run `docker-compose down` then retry |

---

## Evaluation Checklist

| Feature | Implementation |
|---------|---------------|
| ✅ Authentication | JWT with bcrypt, /register + /login |
| ✅ Semantic Search | sentence-transformers + FAISS |
| ✅ ML Classification | TF-IDF + Logistic Regression |
| ✅ Publishability Score | Linear/Ridge Regression (0–1) |
| ✅ MLflow Tracking | 3 runs with params, metrics, artifacts |
| ✅ Prometheus Metrics | 5 counters + latency histogram |
| ✅ Grafana Dashboard | Request rate, latency, errors pre-built |
| ✅ Logging | Rotating file logs in logs/app.log |
| ✅ Caching | In-memory LRU cache for search |
| ✅ Precision@K | /evaluate/precision endpoint |
| ✅ Bibliometrics | /stats endpoint |
| ✅ Docker | Single `docker-compose up` command |
| ✅ REST API | Documented at /docs (Swagger UI) |
