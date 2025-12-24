from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram


SEARCH_REQUESTS_TOTAL = Counter(
    "search_requests_total",
    "Total search requests",
    labelnames=("mode",),
)

SEARCH_DURATION_SECONDS = Histogram(
    "search_duration_seconds",
    "Search duration in seconds",
    labelnames=("mode",),
    buckets=(0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 60),
)

RERANK_DURATION_SECONDS = Histogram(
    "rerank_duration_seconds",
    "Reranker call duration in seconds",
    buckets=(0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10),
)

RERANK_CALLS_TOTAL = Counter("rerank_calls_total", "Total reranker calls")

# Business/product gauges (updated periodically from DB)
TOTAL_USERS = Gauge("app_total_users", "Total users")
ACTIVE_USERS = Gauge("app_active_users", "Active users")
TOTAL_DOCUMENTS = Gauge("app_total_documents", "Total documents")
TOTAL_SEARCHES = Gauge("app_total_searches", "Total searches")
SEARCHES_24H = Gauge("app_searches_24h", "Searches in last 24h")
