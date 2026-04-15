from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Account


class AccountRepositoryImpl:
    """SQLAlchemy implementation of AccountRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, account_id: int) -> Optional[Account]:
        result = await self._session.get(Account, account_id)
        return result

    async def list_by_platform(self, platform: str, status: Optional[str] = None) -> Sequence[Account]:
        stmt = select(Account).where(Account.platform == platform)
        if status:
            stmt = stmt.where(Account.status == status)
        stmt = stmt.order_by(Account.usage_count.asc())
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_active(self, platform: str) -> Sequence[Account]:
        return await self.list_by_platform(platform, status="active")

    async def create(self, account: Account) -> Account:
        self._session.add(account)
        await self._session.flush()
        await self._session.refresh(account)
        return account

    async def update(self, account: Account) -> Account:
        await self._session.flush()
        await self._session.refresh(account)
        return account

    async def delete(self, account_id: int) -> bool:
        account = await self.get_by_id(account_id)
        if not account:
            return False
        await self._session.delete(account)
        await self._session.flush()
        return True
