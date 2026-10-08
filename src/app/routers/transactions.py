from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from src.app.core.dependencies import (
    get_audit_service,
    get_current_active_user,
    get_transaction_service,
)
from src.app.models.user import User
from src.app.schemas.transaction import (
    TransactionCreate,
    TransactionFilterParams,
    TransactionResponse,
    TransactionUpdate,
)
from src.app.services.audit_service import AuditService
from src.app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api/v1/transactions", tags=["Transactions"])


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    data: TransactionCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    service: TransactionService = Depends(get_transaction_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    # Enforces server-side identity: current_user.id
    txn, error = service.create_transaction(user_id=current_user.id, data=data)
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    client_ip = request.client.host if request.client else "unknown"
    audit_service.log(
        event_type="TXN_CREATED",
        resource="/api/v1/transactions",
        status_code=201,
        client_ip=client_ip,
        user_id=current_user.id,
        details={"transaction_id": txn.id, "amount": str(txn.amount), "type": txn.type},
    )
    return txn


@router.get("", response_model=List[TransactionResponse])
def list_transactions(
    keyword: Optional[str] = Query(None, max_length=100, pattern=r"^[a-zA-Z0-9_\-\s]*$"),
    category_id: Optional[int] = Query(None, ge=1),
    type: Optional[str] = Query(None, pattern=r"^(INCOME|EXPENSE)$"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    service: TransactionService = Depends(get_transaction_service),
):
    try:
        filters = TransactionFilterParams(
            keyword=keyword,
            category_id=category_id,
            type=type,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    txns, _ = service.list_transactions(user_id=current_user.id, filters=filters)
    return txns


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    service: TransactionService = Depends(get_transaction_service),
):
    # Compound query lookup
    txn = service.get_transaction(txn_id=transaction_id, user_id=current_user.id)
    if not txn:
        # Uniform 404 response eliminates identifier enumeration (SEC-006)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")
    return txn


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    service: TransactionService = Depends(get_transaction_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    txn, error = service.update_transaction(
        txn_id=transaction_id, user_id=current_user.id, data=data
    )
    if error == "Transaction not found." or (not txn and not error):
        # Uniform 404 on missing or foreign ID
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    client_ip = request.client.host if request.client else "unknown"
    audit_service.log(
        event_type="TXN_UPDATED",
        resource=f"/api/v1/transactions/{transaction_id}",
        status_code=200,
        client_ip=client_ip,
        user_id=current_user.id,
        details={"transaction_id": transaction_id},
    )
    return txn


@router.delete("/{transaction_id}", status_code=status.HTTP_200_OK)
def delete_transaction(
    transaction_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    service: TransactionService = Depends(get_transaction_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    deleted = service.delete_transaction(txn_id=transaction_id, user_id=current_user.id)
    if not deleted:
        # Uniform 404 on missing or foreign ID
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")

    client_ip = request.client.host if request.client else "unknown"
    audit_service.log(
        event_type="TXN_DELETED",
        resource=f"/api/v1/transactions/{transaction_id}",
        status_code=200,
        client_ip=client_ip,
        user_id=current_user.id,
        details={"transaction_id": transaction_id},
    )
    return {"detail": "Transaction deleted successfully."}
