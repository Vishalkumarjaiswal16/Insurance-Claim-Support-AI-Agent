from __future__ import annotations

import sqlite3
from typing import Any

from customer_support_agent.repositories.sqlite.base import connect, row_to_dict


class CustomersRepository:
    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    def create_or_get(
        self,
        email: str,
        name: str | None = None,
        company: str | None = None,
    ) -> dict[str, Any]:
        normalized_email = self._normalize_email(email)

        with connect() as conn:
            # Check if customer already exists
            row = conn.execute(
                "SELECT * FROM customers WHERE lower(email) = ?",
                (normalized_email,),
            ).fetchone()
            if row:
                updates: list[str] = []
                values: list[Any] = []
                if name and not row["name"]:
                    updates.append("name = ?")
                    values.append(name)
                if company and not row["company"]:
                    updates.append("company = ?")
                    values.append(company)
                if updates:
                    values.append(row["id"])
                    conn.execute(f"UPDATE customers SET {', '.join(updates)} WHERE id = ?", values)
                refreshed = conn.execute(
                    "SELECT * FROM customers WHERE id = ?",
                    (row["id"],),
                ).fetchone()
                if refreshed is None:
                    raise RuntimeError(
                        f"Customer with email {normalized_email!r} was not found after update"
                    )
                return row_to_dict(refreshed)

            try:
                conn.execute(
                    "INSERT INTO customers (email, name, company) VALUES (?, ?, ?)",
                    (normalized_email, name, company),
                )
            except sqlite3.IntegrityError as exc:
                # Another thread/process may have inserted the same unique email
                # after the initial SELECT and before this INSERT.
                existing = conn.execute(
                    "SELECT * FROM customers WHERE lower(email) = ?",
                    (normalized_email,),
                ).fetchone()
                if existing is None:
                    raise

            created = conn.execute(
                "SELECT * FROM customers WHERE lower(email) = ?",
                (normalized_email,),
            ).fetchone()
            if created is None:
                raise RuntimeError(
                    f"Customer with email {normalized_email!r} was not found after insert"
                )
            return row_to_dict(created)

    def get_by_id(self, customer_id: int) -> dict[str, Any] | None:
        with connect() as conn:
            row = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
            return row_to_dict(row)

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        normalized_email = self._normalize_email(email)
        with connect() as conn:
            row = conn.execute(
                "SELECT * FROM customers WHERE lower(email) = ?",
                (normalized_email,),
            ).fetchone()
            return row_to_dict(row)
