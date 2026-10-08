"""
Metrics and Monitoring Router for SPEMA.

Exposes standard Prometheus metrics (/metrics) for Kubernetes scraping
and structured JSON metrics (/api/v1/metrics) for monitoring dashboards.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from src.app.core.dependencies import get_current_active_user
from src.app.core.logging import get_recent_security_events
from src.app.core.metrics import metrics
from src.app.models.user import User

router = APIRouter(tags=["Monitoring & Metrics"])


@router.get(
    "/metrics",
    response_class=PlainTextResponse,
    summary="Prometheus Metrics Exposition",
)
def prometheus_metrics() -> PlainTextResponse:
    """Exposes real-time application and security metrics in Prometheus text format."""
    return PlainTextResponse(
        content=metrics.get_prometheus_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@router.get(
    "/api/v1/metrics",
    response_model=Dict[str, Any],
    summary="JSON Operational Metrics Summary",
)
def json_metrics() -> Dict[str, Any]:
    """Exposes JSON-formatted operational and security metrics for health monitors."""
    return metrics.get_metrics_summary()


@router.get(
    "/api/v1/audit/recent-events",
    response_model=List[Dict[str, Any]],
    summary="Recent Structured Security Events",
)
def get_recent_audit_events(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
) -> List[Dict[str, Any]]:
    """
    Returns recent structured security events from the in-memory circular buffer.
    Requires authenticated user access.
    """
    return get_recent_security_events(limit=limit)
