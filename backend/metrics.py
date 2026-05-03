from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# --- Counters ---
total_requests = Counter("research_plus_total_requests", "Total HTTP requests received")
search_requests = Counter("research_plus_search_requests", "Total search requests")
login_requests = Counter("research_plus_login_requests", "Total login requests")
register_requests = Counter("research_plus_register_requests", "Total register requests")
error_count = Counter("research_plus_error_count", "Total errors")

# --- Histograms ---
request_latency = Histogram(
    "research_plus_request_latency_seconds",
    "Request latency in seconds",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)


def metrics_endpoint():
    """Return Prometheus metrics as a plain text response."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
