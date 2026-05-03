import React, { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API = process.env.REACT_APP_API_URL || `http://${window.location.hostname}:8000`;

function api(token) {
  return axios.create({
    baseURL: API,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
}

// ── Tiny components ─────────────────────────────────────────────────────────

function Badge({ cat }) {
  const colors = {
    'Machine Learning': '#7c6dfa',
    'NLP': '#4fc3f7',
    'Computer Vision': '#f7c948',
    'Systems': '#4ade80',
    'Theory': '#f87171',
  };
  return (
    <span className="badge" style={{ background: colors[cat] || '#555' }}>
      {cat}
    </span>
  );
}

function ScoreBar({ score }) {
  const pct = Math.round(score * 100);
  const color = score >= 0.7 ? '#4ade80' : score >= 0.4 ? '#f7c948' : '#f87171';
  return (
    <div className="score-bar-wrap">
      <div className="score-bar" style={{ width: `${pct}%`, background: color }} />
      <span className="score-label" style={{ color }}>{pct}%</span>
    </div>
  );
}

function Spinner() {
  return <div className="spinner" />;
}

// ── Login Screen ─────────────────────────────────────────────────────────────

function LoginScreen({ onLogin }) {
  const [tab, setTab] = useState('login');
  const [form, setForm] = useState({ username: '', password: '', email: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handle = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (tab === 'login') {
        const res = await axios.post(`${API}/login`, { username: form.username, password: form.password });
        onLogin(res.data.access_token, form.username);
      } else {
        await axios.post(`${API}/register`, form);
        setTab('login');
        setError('Registered! Please log in.');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-screen">
      <div className="login-brand">
        <span className="brand-icon">⬡</span>
        <h1>Research<span className="brand-plus">+</span></h1>
        <p>Semantic Research Intelligence Platform</p>
      </div>
      <div className="login-card">
        <div className="tab-row">
          <button className={tab === 'login' ? 'tab active' : 'tab'} onClick={() => setTab('login')}>Login</button>
          <button className={tab === 'register' ? 'tab active' : 'tab'} onClick={() => setTab('register')}>Register</button>
        </div>
        <form onSubmit={handle}>
          <div className="field">
            <label>Username</label>
            <input value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} required placeholder="admin" />
          </div>
          {tab === 'register' && (
            <div className="field">
              <label>Email</label>
              <input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} required placeholder="you@example.com" />
            </div>
          )}
          <div className="field">
            <label>Password</label>
            <input type="password" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} required placeholder="••••••" />
          </div>
          {error && <div className={error.includes('Registered') ? 'msg-success' : 'msg-error'}>{error}</div>}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? <Spinner /> : tab === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>
        <div className="demo-hint">Demo: <code>admin / admin123</code></div>
      </div>
    </div>
  );
}

// ── Search Tab ───────────────────────────────────────────────────────────────

function SearchTab({ token }) {
  const [q, setQ] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const doSearch = async (e) => {
    e.preventDefault();
    if (!q.trim()) return;
    setLoading(true); setError(''); setResults(null);
    try {
      const res = await api(token).get('/search', { params: { q, top_k: 10 } });
      setResults(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="tab-content">
      <h2 className="section-title">Semantic Search</h2>
      <p className="section-sub">Embedding-based similarity search over the paper corpus</p>
      <form onSubmit={doSearch} className="search-form">
        <input
          className="search-input"
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder="e.g. transformer attention mechanism NLP..."
        />
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? <Spinner /> : 'Search'}
        </button>
      </form>
      {error && <div className="msg-error">{error}</div>}
      {results && (
        <div className="results-wrap">
          <div className="results-meta">
            {results.count} results · {results.latency_ms}ms
          </div>
          {results.results.map((p, i) => (
            <div key={p.id} className="paper-card">
              <div className="paper-rank">#{i + 1}</div>
              <div className="paper-body">
                <div className="paper-title">{p.title}</div>
                <div className="paper-meta-row">
                  <Badge cat={p.category || p.predicted_category} />
                  <span className="paper-year">{p.year}</span>
                  <span className="paper-cite">⬆ {p.citations} citations</span>
                  <span className="paper-sim">sim: <strong>{p.similarity_score}</strong></span>
                </div>
                <p className="paper-abstract">{p.abstract?.slice(0, 200)}...</p>
                {p.publishability_score !== undefined && (
                  <div className="pub-row">
                    <span className="pub-label">Publishability</span>
                    <ScoreBar score={p.publishability_score} />
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Papers Tab ───────────────────────────────────────────────────────────────

function PapersTab({ token }) {
  const [papers, setPapers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [cat, setCat] = useState('');
  const [loading, setLoading] = useState(false);

  const CATS = ['', 'Machine Learning', 'NLP', 'Computer Vision', 'Systems', 'Theory'];

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api(token).get('/papers', { params: { page, page_size: 15, category: cat || undefined } });
      setPapers(res.data.papers);
      setTotal(res.data.total);
    } catch (_) {}
    setLoading(false);
  }, [token, page, cat]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="tab-content">
      <h2 className="section-title">Paper Corpus</h2>
      <div className="filter-row">
        {CATS.map(c => (
          <button key={c} className={cat === c ? 'chip active' : 'chip'} onClick={() => { setCat(c); setPage(1); }}>
            {c || 'All'}
          </button>
        ))}
      </div>
      {loading ? <Spinner /> : (
        <>
          <div className="results-meta">{total} papers</div>
          {papers.map(p => (
            <div key={p.id} className="paper-card">
              <div className="paper-rank">#{p.id}</div>
              <div className="paper-body">
                <div className="paper-title">{p.title}</div>
                <div className="paper-meta-row">
                  <Badge cat={p.category} />
                  <span className="paper-year">{p.year}</span>
                  <span className="paper-cite">⬆ {p.citations} citations</span>
                </div>
                {p.publishability_score !== undefined && (
                  <div className="pub-row">
                    <span className="pub-label">Publishability</span>
                    <ScoreBar score={p.publishability_score} />
                  </div>
                )}
              </div>
            </div>
          ))}
          <div className="pagination">
            <button disabled={page === 1} onClick={() => setPage(p => p - 1)} className="btn-sec">← Prev</button>
            <span>Page {page} of {Math.ceil(total / 15)}</span>
            <button disabled={page * 15 >= total} onClick={() => setPage(p => p + 1)} className="btn-sec">Next →</button>
          </div>
        </>
      )}
    </div>
  );
}

// ── ML Tab ───────────────────────────────────────────────────────────────────

function MLTab({ token }) {
  const [title, setTitle] = useState('');
  const [abstract, setAbstract] = useState('');
  const [citations, setCitations] = useState(0);
  const [year, setYear] = useState(2024);
  const [keywords, setKeywords] = useState(5);
  const [cat, setCat] = useState('Machine Learning');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const CATS = ['Machine Learning', 'NLP', 'Computer Vision', 'Systems', 'Theory'];

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true); setResult(null);
    try {
      const res = await api(token).post('/publishability', null, {
        params: { title, abstract, citations, year, keywords, category: cat },
      });
      setResult(res.data);
    } catch (_) {}
    setLoading(false);
  };

  return (
    <div className="tab-content">
      <h2 className="section-title">ML Analysis</h2>
      <p className="section-sub">Predict publishability score using trained Linear Regression model (tracked in MLflow)</p>
      <form onSubmit={submit} className="ml-form">
        <div className="field">
          <label>Paper Title</label>
          <input value={title} onChange={e => setTitle(e.target.value)} required placeholder="A Novel Approach to..." />
        </div>
        <div className="field">
          <label>Abstract</label>
          <textarea value={abstract} onChange={e => setAbstract(e.target.value)} required rows={4} placeholder="We propose a method that..." />
        </div>
        <div className="field-row">
          <div className="field">
            <label>Citations</label>
            <input type="number" min={0} value={citations} onChange={e => setCitations(+e.target.value)} />
          </div>
          <div className="field">
            <label>Year</label>
            <input type="number" min={2000} max={2025} value={year} onChange={e => setYear(+e.target.value)} />
          </div>
          <div className="field">
            <label>Keywords</label>
            <input type="number" min={1} max={20} value={keywords} onChange={e => setKeywords(+e.target.value)} />
          </div>
        </div>
        <div className="field">
          <label>Category</label>
          <select value={cat} onChange={e => setCat(e.target.value)}>
            {CATS.map(c => <option key={c}>{c}</option>)}
          </select>
        </div>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? <Spinner /> : 'Predict Score'}
        </button>
      </form>
      {result && (
        <div className="result-card">
          <div className="result-title">{result.title}</div>
          <Badge cat={result.category} />
          <div className="result-score-big">
            <span>Publishability Score</span>
            <strong style={{ color: result.publishability_score >= 0.7 ? '#4ade80' : result.publishability_score >= 0.4 ? '#f7c948' : '#f87171' }}>
              {Math.round(result.publishability_score * 100)}%
            </strong>
          </div>
          <ScoreBar score={result.publishability_score} />
          <div className={`interp interp-${result.interpretation.toLowerCase()}`}>
            {result.interpretation} Publishability
          </div>
        </div>
      )}
    </div>
  );
}

// ── Stats Tab ────────────────────────────────────────────────────────────────

function StatsTab({ token }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api(token).get('/stats').then(r => { setStats(r.data); setLoading(false); }).catch(() => setLoading(false));
  }, [token]);

  if (loading) return <div className="tab-content"><Spinner /></div>;
  if (!stats) return <div className="tab-content"><div className="msg-error">Failed to load stats</div></div>;

  const cats = Object.entries(stats.categories || {});
  const years = Object.entries(stats.papers_by_year || {}).sort((a, b) => a[0] - b[0]);
  const maxY = Math.max(...years.map(([, v]) => v), 1);

  return (
    <div className="tab-content">
      <h2 className="section-title">Bibliometric Analytics</h2>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-num">{stats.total_papers}</div>
          <div className="stat-name">Total Papers</div>
        </div>
        <div className="stat-card">
          <div className="stat-num">{stats.avg_citations}</div>
          <div className="stat-name">Avg Citations</div>
        </div>
        <div className="stat-card">
          <div className="stat-num">{Math.round(stats.avg_publishability_score * 100)}%</div>
          <div className="stat-name">Avg Pub Score</div>
        </div>
      </div>

      <div className="chart-section">
        <h3>Papers by Category</h3>
        {cats.map(([c, n]) => (
          <div key={c} className="bar-row">
            <span className="bar-label">{c}</span>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${Math.round(n / stats.total_papers * 100)}%` }} />
            </div>
            <span className="bar-count">{n}</span>
          </div>
        ))}
      </div>

      <div className="chart-section">
        <h3>Papers by Year</h3>
        <div className="year-bars">
          {years.map(([y, n]) => (
            <div key={y} className="year-col">
              <div className="year-bar" style={{ height: `${Math.round(n / maxY * 100)}%` }} title={`${y}: ${n}`} />
              <div className="year-label">{y.slice(2)}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="chart-section">
        <h3>Top Cited Papers</h3>
        {stats.top_cited.map((p, i) => (
          <div key={p.id} className="top-paper">
            <span className="top-rank">#{i + 1}</span>
            <span className="top-title">{p.title}</span>
            <span className="top-cite">{p.citations} ↑</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Evaluate Tab ─────────────────────────────────────────────────────────────

function EvalTab({ token }) {
  const [q, setQ] = useState('deep learning image recognition');
  const [cat, setCat] = useState('Computer Vision');
  const [k, setK] = useState(5);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const CATS = ['Machine Learning', 'NLP', 'Computer Vision', 'Systems', 'Theory'];

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true); setResult(null);
    try {
      const res = await api(token).get('/evaluate/precision', { params: { q, category: cat, k } });
      setResult(res.data);
    } catch (_) {}
    setLoading(false);
  };

  return (
    <div className="tab-content">
      <h2 className="section-title">Search Evaluation</h2>
      <p className="section-sub">Compute Precision@K — how many of the top-K results match the expected category</p>
      <form onSubmit={submit} className="ml-form">
        <div className="field">
          <label>Query</label>
          <input value={q} onChange={e => setQ(e.target.value)} required />
        </div>
        <div className="field-row">
          <div className="field">
            <label>Expected Category</label>
            <select value={cat} onChange={e => setCat(e.target.value)}>
              {CATS.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div className="field">
            <label>K</label>
            <input type="number" min={1} max={20} value={k} onChange={e => setK(+e.target.value)} />
          </div>
        </div>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? <Spinner /> : 'Evaluate Precision@K'}
        </button>
      </form>
      {result && (
        <div className="result-card">
          <div className="eval-grid">
            <div><span>Query</span><strong>{result.query}</strong></div>
            <div><span>Category</span><Badge cat={result.category} /></div>
            <div><span>K</span><strong>{result.k}</strong></div>
          </div>
          <div className="result-score-big">
            <span>Precision@{result.k}</span>
            <strong style={{ color: result.precision_at_k >= 0.7 ? '#4ade80' : result.precision_at_k >= 0.4 ? '#f7c948' : '#f87171' }}>
              {Math.round(result.precision_at_k * 100)}%
            </strong>
          </div>
          <ScoreBar score={result.precision_at_k} />
        </div>
      )}
    </div>
  );
}

// ── Main App ─────────────────────────────────────────────────────────────────

const TABS = [
  { id: 'search', label: '⬡ Search' },
  { id: 'papers', label: '◈ Papers' },
  { id: 'ml',     label: '◉ ML Score' },
  { id: 'stats',  label: '▣ Analytics' },
  { id: 'eval',   label: '◇ Evaluate' },
];

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('rp_token') || '');
  const [user, setUser]   = useState(localStorage.getItem('rp_user') || '');
  const [tab, setTab]     = useState('search');

  const onLogin = (tok, username) => {
    setToken(tok); setUser(username);
    localStorage.setItem('rp_token', tok);
    localStorage.setItem('rp_user', username);
  };

  const logout = () => {
    setToken(''); setUser('');
    localStorage.removeItem('rp_token');
    localStorage.removeItem('rp_user');
  };

  if (!token) return <LoginScreen onLogin={onLogin} />;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon">⬡</span>
          <span>Research<span className="brand-plus">+</span></span>
        </div>
        <nav>
          {TABS.map(t => (
            <button
              key={t.id}
              className={tab === t.id ? 'nav-item active' : 'nav-item'}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-chip">
            <span className="user-avatar">{user[0]?.toUpperCase()}</span>
            <span>{user}</span>
          </div>
          <button className="btn-logout" onClick={logout}>Logout</button>
          <div className="ext-links">
            <a href={`http://${window.location.hostname}:3001`} target="_blank" rel="noreferrer">📊 Grafana</a>
            <a href={`http://${window.location.hostname}:5000`} target="_blank" rel="noreferrer">🔬 MLflow</a>
            <a href={`http://${window.location.hostname}:8000/docs`} target="_blank" rel="noreferrer">📖 API Docs</a>
          </div>
        </div>
      </aside>
      <main className="main-content">
        {tab === 'search' && <SearchTab token={token} />}
        {tab === 'papers' && <PapersTab token={token} />}
        {tab === 'ml'     && <MLTab token={token} />}
        {tab === 'stats'  && <StatsTab token={token} />}
        {tab === 'eval'   && <EvalTab token={token} />}
      </main>
    </div>
  );
}