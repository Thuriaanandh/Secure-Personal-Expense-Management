from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.app.core.database import get_db
from src.app.core.dependencies import get_auth_service
from src.app.models.user import User
from src.app.schemas.transaction import TransactionFilterParams
from src.app.services.auth_service import AuthService
from src.app.services.category_service import CategoryService
from src.app.services.transaction_service import TransactionService

# Locate templates directory
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["Web UI"])


def get_optional_web_user(
    request: Request, auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """Helper to retrieve user from cookie without throwing 401 (for UI redirects)."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    return auth_service.get_current_user_from_token(token)


@router.get("/", response_class=HTMLResponse)
def index(request: Request, user: Optional[User] = Depends(get_optional_web_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user: Optional[User] = Depends(get_optional_web_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="login.html")


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, user: Optional[User] = Depends(get_optional_web_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="register.html")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(
    request: Request,
    user: Optional[User] = Depends(get_optional_web_user),
    db: Session = Depends(get_db),
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    txn_service = TransactionService(db)
    now = datetime.now()
    summary = txn_service.get_monthly_summary(user_id=user.id, year=now.year, month=now.month)

    # Get 5 most recent transactions
    filters = TransactionFilterParams(skip=0, limit=5)
    recent_transactions, _ = txn_service.list_transactions(user_id=user.id, filters=filters)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "active_page": "dashboard",
            "user": user,
            "summary": summary,
            "recent_transactions": recent_transactions,
        },
    )


@router.get("/transactions", response_class=HTMLResponse)
def transactions_page(
    request: Request,
    keyword: Optional[str] = None,
    type: Optional[str] = None,
    category_id: Optional[int] = None,
    start_date: Optional[date] = None,
    user: Optional[User] = Depends(get_optional_web_user),
    db: Session = Depends(get_db),
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    txn_service = TransactionService(db)
    cat_service = CategoryService(db)

    categories = cat_service.list_categories(user_id=user.id)
    filters = TransactionFilterParams(
        keyword=keyword, type=type, category_id=category_id, start_date=start_date, skip=0, limit=50
    )
    transactions, total_count = txn_service.list_transactions(user_id=user.id, filters=filters)

    return templates.TemplateResponse(
        request=request,
        name="transactions.html",
        context={
            "active_page": "transactions",
            "user": user,
            "transactions": transactions,
            "categories": categories,
            "keyword": keyword,
            "current_type": type,
            "current_cat": category_id,
            "start_date": start_date,
            "total_count": total_count,
        },
    )


@router.get("/reports", response_class=HTMLResponse)
def reports_page(
    request: Request,
    user: Optional[User] = Depends(get_optional_web_user),
    db: Session = Depends(get_db),
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    cat_service = CategoryService(db)
    categories = cat_service.list_categories(user_id=user.id)

    return templates.TemplateResponse(
        request=request,
        name="reports.html",
        context={"active_page": "reports", "user": user, "categories": categories},
    )
