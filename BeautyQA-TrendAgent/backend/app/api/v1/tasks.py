from __future__ import annotations

from typing import Optional

from celery import chain
from fastapi import APIRouter, HTTPException

from app.api.deps import TaskServiceDep, KeywordServiceDep, CrawlerAdapterDep
from app.domain.models.crawl_task import CrawlTaskCreate, CrawlTaskRead, CrawlTaskLogRead
from app.tasks.crawl_tasks import crawl_platform
from app.tasks.clean_tasks import process_trend_data

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=CrawlTaskRead, status_code=201)
async def create_task(
    data: CrawlTaskCreate,
    service: TaskServiceDep,
    keyword_service: KeywordServiceDep,
):
    """Create a new crawl task (does not start it automatically)."""
    keyword = await keyword_service.get_keyword(data.keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return await service.create_task(data, keyword.keyword)


@router.post("/{task_id}/start", response_model=dict)
async def start_task(task_id: int, service: TaskServiceDep, adapter: CrawlerAdapterDep):
    """Start a pending crawl task by dispatching a Celery chain: crawl -> clean."""
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "pending":
        raise HTTPException(status_code=400, detail=f"Task is {task.status}, not pending")

    # Dispatch Celery chain
    task_chain = chain(
        crawl_platform.s(task_id),
        process_trend_data.s(),
    )
    result = task_chain.apply_async()

    return {
        "task_id": task_id,
        "celery_chain_id": result.id,
        "status": "dispatched",
    }


@router.post("/{task_id}/cancel", response_model=CrawlTaskRead)
async def cancel_task(task_id: int, service: TaskServiceDep, adapter: CrawlerAdapterDep):
    """Cancel a running task."""
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status not in ("pending", "running"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel task in {task.status} state")

    # Stop the crawler subprocess if running
    if task.status == "running":
        await adapter.stop_crawl(task_id)

    result = await service.mark_cancelled(task_id)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to cancel task")
    return result


@router.get("", response_model=list[CrawlTaskRead])
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    service: TaskServiceDep = None,
):
    """List crawl tasks."""
    return await service.list_tasks(status, limit, offset)


@router.get("/{task_id}", response_model=CrawlTaskRead)
async def get_task(task_id: int, service: TaskServiceDep):
    """Get task details."""
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/{task_id}/logs", response_model=list[CrawlTaskLogRead])
async def get_task_logs(task_id: int, limit: int = 100, service: TaskServiceDep = None):
    """Get task execution logs."""
    return await service._repo.get_logs(task_id, limit)
