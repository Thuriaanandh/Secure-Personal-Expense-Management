from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from src.app.core.dependencies import (
    get_audit_service,
    get_current_active_user,
    get_reporting_service,
    get_transaction_service,
)
from src.app.models.user import User
from src.app.schemas.transaction import MonthlySummaryResponse, TransactionFilterParams
from src.app.services.audit_service import AuditService
from src.app.services.reporting_service import ReportingService
from src.app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


@router.get("/summary", response_model=MonthlySummaryResponse)
def get_monthly_summary(
    year: Optional[int] = Query(None, ge=2000, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    current_user: User = Depends(get_current_active_user),
    service: TransactionService = Depends(get_transaction_service),
):
    now = datetime.now()
    target_year = year or now.year
    target_month = month or now.month

    summary_data = service.get_monthly_summary(
        user_id=current_user.id, year=target_year, month=target_month
    )
    return summary_data


@router.get("/export-csv")
def export_csv_report(
    request: Request,
    keyword: Optional[str] = Query(None, max_length=100, pattern=r"^[a-zA-Z0-9_\-\s]*$"),
    category_id: Optional[int] = Query(None, ge=1),
    type: Optional[str] = Query(None, pattern=r"^(INCOME|EXPENSE)$"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_active_user),
    reporting_service: ReportingService = Depends(get_reporting_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    try:
        filters = TransactionFilterParams(
            keyword=keyword,
            category_id=category_id,
            type=type,
            start_date=start_date,
            end_date=end_date,
            skip=0,
            limit=100,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    csv_buffer = reporting_service.generate_csv_report(user_id=current_user.id, filters=filters)

    client_ip = request.client.host if request.client else "unknown"
    audit_service.log(
        event_type="REPORT_EXPORTED",
        resource="/api/v1/reports/export-csv",
        status_code=200,
        client_ip=client_ip,
        user_id=current_user.id,
        details={"type": type, "category_id": category_id},
    )

    filename = f"expense_report_{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([csv_buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export-json")
def export_json_report(
    request: Request,
    keyword: Optional[str] = Query(None, max_length=100, pattern=r"^[a-zA-Z0-9_\-\s]*$"),
    category_id: Optional[int] = Query(None, ge=1),
    type: Optional[str] = Query(None, pattern=r"^(INCOME|EXPENSE)$"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_active_user),
    reporting_service: ReportingService = Depends(get_reporting_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    try:
        filters = TransactionFilterParams(
            keyword=keyword,
            category_id=category_id,
            type=type,
            start_date=start_date,
            end_date=end_date,
            skip=0,
            limit=100,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    data = reporting_service.generate_json_report(user_id=current_user.id, filters=filters)

    client_ip = request.client.host if request.client else "unknown"
    audit_service.log(
        event_type="REPORT_EXPORTED_JSON",
        resource="/api/v1/reports/export-json",
        status_code=200,
        client_ip=client_ip,
        user_id=current_user.id,
        details={"type": type, "category_id": category_id},
    )

    return data
