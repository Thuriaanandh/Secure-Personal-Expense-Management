import csv
import io
from typing import Optional

from sqlalchemy.orm import Session

from src.app.repositories.transaction_repository import TransactionRepository
from src.app.schemas.transaction import TransactionFilterParams

FORMULA_TRIGGERS = ("=", "+", "-", "@", "\t", "\r")


def sanitize_csv_cell(value: any) -> str:
    """
    Neutralize spreadsheet formula injection (CWE-1236).
    Prepends single quote (') if the string begins with =, +, -, @, tab, or CR.
    """
    if value is None:
        return ""
    str_val = str(value)
    if str_val.startswith(FORMULA_TRIGGERS):
        return f"'{str_val}"
    return str_val


class ReportingService:
    def __init__(self, db: Session):
        self.db = db
        self.txn_repo = TransactionRepository(db)

    def generate_csv_report(
        self, user_id: int, filters: Optional[TransactionFilterParams] = None
    ) -> io.StringIO:
        """
        Exports CSV strictly scoped to user_id.
        All cells are sanitized against spreadsheet formula injection.
        """
        # Retrieve transactions (ignoring pagination limits for report export)
        export_filters = None
        if filters:
            export_filters = filters.model_copy()
            export_filters.skip = 0
            export_filters.limit = 10000  # Cap at 10,000 to prevent unbounded memory DoS

        transactions, _ = self.txn_repo.list_user_transactions(
            user_id=user_id, filters=export_filters
        )

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(["Date", "Type", "Category", "Amount", "Description"])

        for item in transactions:
            writer.writerow(
                [
                    item.transaction_date.strftime("%Y-%m-%d"),
                    sanitize_csv_cell(item.type),
                    sanitize_csv_cell(item.category.name if item.category else "Uncategorized"),
                    f"{item.amount:.2f}",
                    sanitize_csv_cell(item.description or ""),
                ]
            )

        output.seek(0)
        return output

    def generate_json_report(
        self, user_id: int, filters: Optional[TransactionFilterParams] = None
    ) -> list:
        """
        Exports JSON strictly scoped to user_id.
        """
        export_filters = None
        if filters:
            export_filters = filters.model_copy()
            export_filters.skip = 0
            export_filters.limit = 10000

        transactions, _ = self.txn_repo.list_user_transactions(
            user_id=user_id, filters=export_filters
        )
        return [
            {
                "id": item.id,
                "date": item.transaction_date.strftime("%Y-%m-%d"),
                "type": item.type,
                "category": item.category.name if item.category else "Uncategorized",
                "amount": float(item.amount),
                "description": item.description or "",
            }
            for item in transactions
        ]
