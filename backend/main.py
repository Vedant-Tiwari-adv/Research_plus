import time
import os
import io
import pandas as pd
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

import metrics as m
from auth import (
    UserRegister, UserLogin, Token,
    register_user, login_user, get_current_user, seed_demo_user,
)
from search import get_search_engine
from classifier import get_classifier
from publishability import get_pub_model
from logger import get_logger, TimedLogger

logger = get_logger("main")
def _resolve_data_path():
    env = os.getenv("DATA_PATH", "")
    if env:
        return env
    _here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(_here, "papers.csv"),
        os.path.join(_here, "..", "data", "papers.csv"),
        os.path.join(_here, "data", "papers.csv"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return os.path.normpath(p)
    return "/app/data/papers.csv"

DATA_PATH = _resolve_data_path()


# ── Startup / shutdown ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== Research+ starting up ===")
    seed_demo_user()

    df = pd.read_csv(DATA_PATH)
    logger.info(f"Loaded {len(df)} papers from {DATA_PATH}")

    clf = get_classifier()
    clf.train(df)

    pub = get_pub_model()
    pub.train_all_runs(df)

    predicted_cats = clf.predict_batch(df)
    df["predicted_category"] = predicted_cats
    pub_scores = pub.predict_batch(df)
    df["publishability_score"] = pub_scores

    se = get_search_engine()
    se.build_index(df)

    app.state.df = df
    logger.info("=== Research+ ready ===")
    yield
    logger.info("=== Research+ shutting down ===")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Research+ : Semantic Research Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Middleware: metrics + latency ─────────────────────────────────────────────
@app.middleware("http")
async def track_metrics(request, call_next):
    m.total_requests.inc()
    start = time.perf_counter()
    try:
        response = await call_next(request)
        if response.status_code >= 500:
            m.error_count.inc()
        return response
    except Exception:
        m.error_count.inc()
        raise
    finally:
        latency = time.perf_counter() - start
        m.request_latency.observe(latency)


# ── Auth endpoints ────────────────────────────────────────────────────────────
@app.post("/register", tags=["Auth"])
def register(payload: UserRegister):
    m.register_requests.inc()
    return register_user(payload)


@app.post("/login", response_model=Token, tags=["Auth"])
def login(payload: UserLogin):
    m.login_requests.inc()
    return login_user(payload)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "Research+"}


# ── Metrics ───────────────────────────────────────────────────────────────────
@app.get("/metrics", tags=["System"], include_in_schema=False)
def prometheus_metrics():
    return m.metrics_endpoint()


# ── Search ────────────────────────────────────────────────────────────────────
@app.get("/search", tags=["Core"])
def search(
    q: str = Query(..., min_length=2, description="Search query"),
    top_k: int = Query(10, ge=1, le=50),
    current_user: str = Depends(get_current_user),
):
    m.search_requests.inc()
    se = get_search_engine()
    with TimedLogger(logger, f"search('{q}')") as tl:
        results = se.search(q, top_k=top_k)
    return {
        "query": q,
        "top_k": top_k,
        "count": len(results),
        "latency_ms": round(tl.elapsed_ms, 2),
        "results": results,
    }


# ── Papers listing ────────────────────────────────────────────────────────────
@app.get("/papers", tags=["Core"])
def list_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str = Query(None),
    current_user: str = Depends(get_current_user),
):
    df: pd.DataFrame = app.state.df
    if category:
        df = df[df["category"] == category]
    total = len(df)
    start = (page - 1) * page_size
    end = start + page_size
    records = df.iloc[start:end].to_dict(orient="records")
    return {"total": total, "page": page, "page_size": page_size, "papers": records}


# ── Single paper ──────────────────────────────────────────────────────────────
@app.get("/papers/{paper_id}", tags=["Core"])
def get_paper(paper_id: int, current_user: str = Depends(get_current_user)):
    df: pd.DataFrame = app.state.df
    row = df[df["id"] == paper_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Paper not found")
    return row.iloc[0].to_dict()


# ── Classify a custom paper ───────────────────────────────────────────────────
@app.post("/classify", tags=["ML"])
def classify_paper(
    title: str,
    abstract: str,
    current_user: str = Depends(get_current_user),
):
    clf = get_classifier()
    category = clf.predict(title, abstract)
    return {"title": title, "predicted_category": category}


# ── Publishability score for custom paper ─────────────────────────────────────
@app.post("/publishability", tags=["ML"])
def score_paper(
    title: str,
    abstract: str,
    citations: int = 0,
    year: int = 2024,
    keywords: int = 5,
    category: str = "Machine Learning",
    current_user: str = Depends(get_current_user),
):
    pub = get_pub_model()
    score = pub.predict_score(title, abstract, citations, year, keywords, category)
    return {
        "title": title,
        "publishability_score": score,
        "category": category,
        "interpretation": (
            "High" if score >= 0.7 else
            "Medium" if score >= 0.4 else
            "Low"
        ),
    }


# ── Validation: Precision@K ───────────────────────────────────────────────────
@app.get("/evaluate/precision", tags=["Evaluation"])
def evaluate_precision(
    q: str = Query(...),
    category: str = Query(...),
    k: int = Query(5, ge=1, le=20),
    current_user: str = Depends(get_current_user),
):
    se = get_search_engine()
    p_at_k = se.precision_at_k(q, category, k)
    return {"query": q, "category": category, "k": k, "precision_at_k": p_at_k}


# ── Upload CSV ────────────────────────────────────────────────────────────────
REQUIRED_COLS = {"title", "abstract", "year", "citations", "keywords", "category"}

@app.post("/upload-csv", tags=["Core"])
async def upload_csv(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    contents = await file.read()
    try:
        new_df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    missing = REQUIRED_COLS - set(new_df.columns.str.lower())
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV is missing required columns: {', '.join(sorted(missing))}",
        )

    # Normalise column names to lowercase
    new_df.columns = new_df.columns.str.lower()

    # Drop rows with null title/abstract
    new_df = new_df.dropna(subset=["title", "abstract"])
    if new_df.empty:
        raise HTTPException(status_code=400, detail="CSV has no valid rows after dropping nulls")

    existing_df: pd.DataFrame = app.state.df

    # Assign new IDs continuing from current max
    start_id = int(existing_df["id"].max()) + 1 if "id" in existing_df.columns else 1
    new_df = new_df.reset_index(drop=True)
    new_df["id"] = range(start_id, start_id + len(new_df))

    # Fill optional numeric cols with sensible defaults
    for col, default in [("year", 2024), ("citations", 0), ("keywords", 5)]:
        new_df[col] = pd.to_numeric(new_df[col], errors="coerce").fillna(default).astype(int)

    clf = get_classifier()
    pub = get_pub_model()
    se  = get_search_engine()

    predicted_cats = clf.predict_batch(new_df)
    new_df["predicted_category"] = predicted_cats
    pub_scores = pub.predict_batch(new_df)
    new_df["publishability_score"] = pub_scores

    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    app.state.df = combined_df

    # Rebuild FAISS index with full corpus
    se.add_papers(new_df)

    logger.info(
        f"CSV upload by '{current_user}': {len(new_df)} new papers added "
        f"(total now {len(combined_df)})"
    )
    return {
        "message": "CSV uploaded and index rebuilt",
        "rows_added": len(new_df),
        "total_papers": len(combined_df),
        "new_ids": [int(i) for i in new_df["id"].tolist()],
    }


# ── Bibliometric stats ────────────────────────────────────────────────────────
@app.get("/stats", tags=["Analytics"])
def bibliometric_stats(current_user: str = Depends(get_current_user)):
    df: pd.DataFrame = app.state.df
    cat_counts = df["category"].value_counts().to_dict()
    year_counts = df["year"].value_counts().sort_index().to_dict()
    avg_citations = float(df["citations"].mean())
    avg_pub_score = float(df["publishability_score"].mean()) if "publishability_score" in df.columns else 0.0
    return {
        "total_papers": len(df),
        "categories": cat_counts,
        "papers_by_year": {str(k): v for k, v in year_counts.items()},
        "avg_citations": round(avg_citations, 2),
        "avg_publishability_score": round(avg_pub_score, 4),
        "top_cited": df.nlargest(5, "citations")[["id", "title", "citations"]].to_dict(orient="records"),
    }