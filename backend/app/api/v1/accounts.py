from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException

from app.api.deps import AccountServiceDep
from app.domain.models.account import AccountCreate, AccountUpdate, AccountRead

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountRead, status_code=201)
async def create_account(data: AccountCreate, service: AccountServiceDep):
    """Add a new platform account."""
    return await service.create_account(data)


@router.get("", response_model=list[AccountRead])
async def list_accounts(
    platform: str,
    status: Optional[str] = None,
    service: AccountServiceDep = None,
):
    """List accounts for a platform."""
    return await service.list_accounts(platform, status)


@router.get("/{account_id}", response_model=AccountRead)
async def get_account(account_id: int, service: AccountServiceDep):
    """Get account by ID."""
    account = await service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.patch("/{account_id}", response_model=AccountRead)
async def update_account(account_id: int, data: AccountUpdate, service: AccountServiceDep):
    """Update an account."""
    account = await service.update_account(account_id, data)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.delete("/{account_id}", status_code=204)
async def delete_account(account_id: int, service: AccountServiceDep):
    """Delete an account."""
    if not await service.delete_account(account_id):
        raise HTTPException(status_code=404, detail="Account not found")
