from __future__ import annotations

from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_session
from app.infrastructure.repositories.account_repo_impl import AccountRepositoryImpl
from app.infrastructure.repositories.keyword_repo_impl import KeywordRepositoryImpl
from app.infrastructure.repositories.task_repo_impl import TaskRepositoryImpl
from app.infrastructure.repositories.trend_repo_impl import TrendRepositoryImpl
from app.domain.services.account_service import AccountService
from app.domain.services.keyword_service import KeywordService
from app.domain.services.task_service import TaskService
from app.infrastructure.crawler.adapter import CrawlerAdapter


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_account_service(session: SessionDep) -> AccountService:
    repo = AccountRepositoryImpl(session)
    return AccountService(repo)


def get_keyword_service(session: SessionDep) -> KeywordService:
    repo = KeywordRepositoryImpl(session)
    return KeywordService(repo)


def get_task_service(session: SessionDep) -> TaskService:
    repo = TaskRepositoryImpl(session)
    return TaskService(repo)


def get_trend_repo(session: SessionDep) -> TrendRepositoryImpl:
    return TrendRepositoryImpl(session)


def get_crawler_adapter() -> CrawlerAdapter:
    return CrawlerAdapter()


AccountServiceDep = Annotated[AccountService, Depends(get_account_service)]
KeywordServiceDep = Annotated[KeywordService, Depends(get_keyword_service)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
TrendRepoDep = Annotated[TrendRepositoryImpl, Depends(get_trend_repo)]
CrawlerAdapterDep = Annotated[CrawlerAdapter, Depends(get_crawler_adapter)]
