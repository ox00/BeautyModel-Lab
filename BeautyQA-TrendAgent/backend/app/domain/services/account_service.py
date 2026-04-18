from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Sequence

from app.domain.models.account import AccountCreate, AccountUpdate, AccountRead
from app.domain.services.account_runtime import normalize_account_platform
from app.infrastructure.database.models import Account
from app.infrastructure.repositories.account_repo_impl import AccountRepositoryImpl

logger = logging.getLogger(__name__)


class AccountService:
    """Domain service for managing platform accounts."""

    def __init__(self, repo: AccountRepositoryImpl) -> None:
        self._repo = repo

    async def create_account(self, data: AccountCreate) -> AccountRead:
        account = Account(
            platform=normalize_account_platform(data.platform),
            cookies=data.cookies,
            login_type=data.login_type,
            rotation_strategy=data.rotation_strategy,
            remark=data.remark,
        )
        account = await self._repo.create(account)
        return AccountRead.model_validate(account)

    async def update_account(self, account_id: int, data: AccountUpdate) -> Optional[AccountRead]:
        account = await self._repo.get_by_id(account_id)
        if not account:
            return None
        if data.cookies is not None:
            account.cookies = data.cookies
        if data.login_type is not None:
            account.login_type = data.login_type
        if data.status is not None:
            account.status = data.status
        if data.rotation_strategy is not None:
            account.rotation_strategy = data.rotation_strategy
        if data.remark is not None:
            account.remark = data.remark
        account = await self._repo.update(account)
        return AccountRead.model_validate(account)

    async def delete_account(self, account_id: int) -> bool:
        return await self._repo.delete(account_id)

    async def get_account(self, account_id: int) -> Optional[AccountRead]:
        account = await self._repo.get_by_id(account_id)
        return AccountRead.model_validate(account) if account else None

    async def list_accounts(self, platform: str, status: Optional[str] = None) -> list[AccountRead]:
        accounts = await self._repo.list_by_platform(normalize_account_platform(platform), status)
        return [AccountRead.model_validate(a) for a in accounts]

    async def pick_account_for_crawl(self, platform: str) -> Optional[Account]:
        """Pick the best available account for a crawl task using rotation strategy."""
        active_accounts = await self._repo.list_active(normalize_account_platform(platform))
        if not active_accounts:
            return None

        # Simple round-robin: pick the one with lowest usage_count
        best = min(active_accounts, key=lambda a: a.usage_count)
        best.usage_count += 1
        best.last_used_at = datetime.now()
        await self._repo.update(best)
        return best
