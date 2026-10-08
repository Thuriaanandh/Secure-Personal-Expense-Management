"""
Application and Security Metrics Registry for SPEMA.

Tracks real-time operational and security-relevant counters, gauges, and request rates.
Exposes both Prometheus exposition format and JSON metrics summary endpoints.
"""

import time
from collections import defaultdict
from threading import Lock
from typing import Any, Dict


class MetricsRegistry:
    def __init__(self):
        self._lock = Lock()
        self.start_time = time.time()
        self.auth_successes_total = 0
        self.auth_failures_total = 0
        self.authz_failures_total = 0
        self.rate_limit_exceeded_total = 0
        self.transactions_created_total = 0
        self.transactions_deleted_total = 0
        self.reports_generated_total = 0
        self.server_errors_total = 0
        self.http_requests_total: Dict[str, int] = defaultdict(int)

    def record_auth_success(self):
        with self._lock:
            self.auth_successes_total += 1

    def record_auth_failure(self):
        with self._lock:
            self.auth_failures_total += 1

    def record_authz_failure(self):
        with self._lock:
            self.authz_failures_total += 1

    def record_rate_limit_exceeded(self):
        with self._lock:
            self.rate_limit_exceeded_total += 1

    def record_transaction_created(self):
        with self._lock:
            self.transactions_created_total += 1

    def record_transaction_deleted(self):
        with self._lock:
            self.transactions_deleted_total += 1

    def record_report_generated(self):
        with self._lock:
            self.reports_generated_total += 1

    def record_server_error(self):
        with self._lock:
            self.server_errors_total += 1

    def record_http_request(self, method: str, status_code: int):
        with self._lock:
            key = f"{method.upper()}_{status_code}"
            self.http_requests_total[key] += 1

    def get_uptime_seconds(self) -> float:
        return round(time.time() - self.start_time, 2)

    def get_metrics_summary(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "status": "operational",
                "uptime_seconds": self.get_uptime_seconds(),
                "counters": {
                    "auth_successes_total": self.auth_successes_total,
                    "auth_failures_total": self.auth_failures_total,
                    "authz_failures_total": self.authz_failures_total,
                    "rate_limit_exceeded_total": self.rate_limit_exceeded_total,
                    "transactions_created_total": self.transactions_created_total,
                    "transactions_deleted_total": self.transactions_deleted_total,
                    "reports_generated_total": self.reports_generated_total,
                    "server_errors_total": self.server_errors_total,
                },
                "http_requests_by_status": dict(self.http_requests_total),
            }

    def get_prometheus_metrics(self) -> str:
        with self._lock:
            lines = [
                "# HELP spema_app_uptime_seconds Application uptime in seconds",
                "# TYPE spema_app_uptime_seconds gauge",
                f"spema_app_uptime_seconds {self.get_uptime_seconds()}",
                "",
                "# HELP spema_auth_successes_total Total successful user authentications",
                "# TYPE spema_auth_successes_total counter",
                f"spema_auth_successes_total {self.auth_successes_total}",
                "",
                "# HELP spema_auth_failures_total Total failed authentication attempts",
                "# TYPE spema_auth_failures_total counter",
                f"spema_auth_failures_total {self.auth_failures_total}",
                "",
                "# HELP spema_authz_failures_total Total authorization failures and IDOR attempts",
                "# TYPE spema_authz_failures_total counter",
                f"spema_authz_failures_total {self.authz_failures_total}",
                "",
                "# HELP spema_rate_limit_exceeded_total Total rate limit lockout events",
                "# TYPE spema_rate_limit_exceeded_total counter",
                f"spema_rate_limit_exceeded_total {self.rate_limit_exceeded_total}",
                "",
                "# HELP spema_transactions_created_total Total financial transactions created",
                "# TYPE spema_transactions_created_total counter",
                f"spema_transactions_created_total {self.transactions_created_total}",
                "",
                "# HELP spema_transactions_deleted_total Total financial transactions deleted",
                "# TYPE spema_transactions_deleted_total counter",
                f"spema_transactions_deleted_total {self.transactions_deleted_total}",
                "",
                "# HELP spema_reports_generated_total Total financial reports exported",
                "# TYPE spema_reports_generated_total counter",
                f"spema_reports_generated_total {self.reports_generated_total}",
                "",
                "# HELP spema_server_errors_total Total 5xx internal server errors",
                "# TYPE spema_server_errors_total counter",
                f"spema_server_errors_total {self.server_errors_total}",
                "",
                "# HELP spema_http_requests_total Total HTTP requests handled by method and status",
                "# TYPE spema_http_requests_total counter",
            ]
            for key, val in sorted(self.http_requests_total.items()):
                parts = key.split("_")
                method = parts[0]
                status_code = parts[1] if len(parts) > 1 else "unknown"
                lines.append(
                    f'spema_http_requests_total{{method="{method}",status="{status_code}"}} {val}'
                )

            return "\n".join(lines) + "\n"

    def reset(self):
        with self._lock:
            self.auth_successes_total = 0
            self.auth_failures_total = 0
            self.authz_failures_total = 0
            self.rate_limit_exceeded_total = 0
            self.transactions_created_total = 0
            self.transactions_deleted_total = 0
            self.reports_generated_total = 0
            self.server_errors_total = 0
            self.http_requests_total.clear()


# Global Singleton Metrics Registry
metrics = MetricsRegistry()
