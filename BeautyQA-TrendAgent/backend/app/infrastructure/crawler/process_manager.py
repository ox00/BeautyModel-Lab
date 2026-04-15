from __future__ import annotations

import asyncio
import logging
import os
import signal
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from app.infrastructure.crawler.config_mapper import CrawlCommand

logger = logging.getLogger(__name__)


class ProcessStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CrawlResult:
    """Result of a crawl subprocess execution."""

    exit_code: int
    stdout: str
    stderr: str
    started_at: datetime
    completed_at: datetime
    status: ProcessStatus

    @property
    def is_success(self) -> bool:
        return self.exit_code == 0


@dataclass
class ManagedProcess:
    """Tracks a single MediaCrawler subprocess."""

    process_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    process: Optional[asyncio.subprocess.Process] = None
    status: ProcessStatus = ProcessStatus.IDLE
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    stdout_lines: list[str] = field(default_factory=list)
    stderr_lines: list[str] = field(default_factory=list)
    command: Optional[CrawlCommand] = None
    _read_task: Optional[asyncio.Task] = None


class CrawlerProcessManager:
    """Manages MediaCrawler subprocess lifecycle.

    Each crawl task runs in its own subprocess to ensure full isolation
    from the main application and avoid global config conflicts in MediaCrawler.
    """

    def __init__(self) -> None:
        self._processes: dict[str, ManagedProcess] = {}
        self._lock = asyncio.Lock()

    async def start_crawl(self, command: CrawlCommand, task_id: str) -> ManagedProcess:
        """Start a crawl subprocess.

        Args:
            command: The CLI command to execute.
            task_id: Business-level task ID for tracking.

        Returns:
            ManagedProcess tracking object.
        """
        async with self._lock:
            mp = ManagedProcess(command=command)
            self._processes[task_id] = mp

            mp.started_at = datetime.now()
            mp.status = ProcessStatus.RUNNING

            try:
                mp.process = await asyncio.create_subprocess_exec(
                    *command.command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=command.cwd,
                    env={**_get_env(), "PYTHONUNBUFFERED": "1"},
                )

                # Start async readers
                mp._read_task = asyncio.create_task(self._read_output(mp))

            except Exception as e:
                mp.status = ProcessStatus.FAILED
                mp.stderr_lines.append(f"Failed to start process: {e}")
                mp.completed_at = datetime.now()

            return mp

    async def stop_crawl(self, task_id: str, timeout: float = 15.0) -> bool:
        """Stop a running crawl subprocess gracefully.

        On Windows, kills the entire process tree (Python + Playwright browser)
        to prevent orphaned browser processes that could lock the data directory
        and cause subsequent subprocess launches to hang.

        Args:
            task_id: The task ID to stop.
            timeout: Seconds to wait for graceful exit before force-killing.

        Returns:
            True if the process was stopped, False if not found or already stopped.
        """
        async with self._lock:
            mp = self._processes.get(task_id)
            if not mp or not mp.process or mp.process.returncode is not None:
                return False

            mp.status = ProcessStatus.STOPPING
            pid = mp.process.pid

            if os.name == "nt":
                # Windows: use taskkill /F /T /PID to kill the entire process tree.
                # This ensures Playwright browser child processes are also
                # terminated, preventing orphaned browsers that lock the
                # user-data-dir and block subsequent launches.
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        capture_output=True,
                        timeout=10,
                    )
                except Exception as e:
                    logger.warning(f"[ProcessManager] taskkill failed for PID {pid}: {e}")
                    # Fallback to standard kill
                    try:
                        mp.process.kill()
                    except ProcessLookupError:
                        pass
            else:
                # Unix: send SIGTERM first, then SIGKILL after timeout
                try:
                    mp.process.send_signal(signal.SIGTERM)
                except ProcessLookupError:
                    pass

                try:
                    await asyncio.wait_for(mp.process.wait(), timeout=timeout)
                except asyncio.TimeoutError:
                    try:
                        mp.process.kill()
                    except ProcessLookupError:
                        pass

            # Wait briefly for the process to fully exit
            try:
                await asyncio.wait_for(mp.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                pass

            mp.status = ProcessStatus.FAILED
            mp.completed_at = datetime.now()
            return True

    def get_status(self, task_id: str) -> Optional[ProcessStatus]:
        """Get the status of a managed process."""
        mp = self._processes.get(task_id)
        return mp.status if mp else None

    def get_process(self, task_id: str) -> Optional[ManagedProcess]:
        """Get a managed process by task ID."""
        return self._processes.get(task_id)

    async def wait_for_completion(self, task_id: str, timeout: float = 600.0) -> Optional[CrawlResult]:
        """Wait for a crawl subprocess to complete and return the result.

        Args:
            task_id: The task ID to wait for.
            timeout: Maximum seconds to wait (default 10 minutes).

        Returns:
            CrawlResult or None if process not found.
        """
        mp = self._processes.get(task_id)
        if not mp or not mp.process:
            return None

        try:
            exit_code = await asyncio.wait_for(mp.process.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"[ProcessManager] Subprocess {task_id} timed out after {timeout}s, stopping...")
            await self.stop_crawl(task_id)
            exit_code = -1

        # Wait for reader task to finish
        if mp._read_task and not mp._read_task.done():
            try:
                await asyncio.wait_for(mp._read_task, timeout=5.0)
            except asyncio.TimeoutError:
                mp._read_task.cancel()

        mp.completed_at = datetime.now()
        mp.status = ProcessStatus.COMPLETED if exit_code == 0 else ProcessStatus.FAILED

        # Log subprocess output summary for debugging
        if mp.stdout_lines:
            logger.info(f"[ProcessManager] Subprocess {task_id} stdout ({len(mp.stdout_lines)} lines): "
                        f"last={mp.stdout_lines[-1][:200]}")
        if mp.stderr_lines:
            logger.info(f"[ProcessManager] Subprocess {task_id} stderr ({len(mp.stderr_lines)} lines): "
                        f"last={mp.stderr_lines[-1][:200]}")

        return CrawlResult(
            exit_code=exit_code,
            stdout="\n".join(mp.stdout_lines),
            stderr="\n".join(mp.stderr_lines),
            started_at=mp.started_at or datetime.now(),
            completed_at=mp.completed_at,
            status=mp.status,
        )

    async def _read_output(self, mp: ManagedProcess) -> None:
        """Read stdout and stderr from a subprocess concurrently."""
        if not mp.process:
            return

        async def _read_stream(stream, target_list):
            while True:
                try:
                    line = await stream.readline()
                except Exception:
                    break
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace").rstrip()
                if decoded:
                    target_list.append(decoded)
                    # Forward key subprocess output to pipeline log in real-time
                    # Only log lines that contain useful status info (not noise)
                    if any(kw in decoded for kw in ["search", "note", "comment", "error", "Error", "fail", "finish", "complete", "start", "login"]):
                        logger.debug(f"[MC] {decoded[:200]}")

        await asyncio.gather(
            _read_stream(mp.process.stdout, mp.stdout_lines),
            _read_stream(mp.process.stderr, mp.stderr_lines),
        )


def _get_env() -> dict:
    """Get a copy of the current environment variables,
    with MediaCrawler-required DB settings injected from .env."""
    import os
    from app.config.settings import settings

    env = dict(os.environ)

    # Ensure MediaCrawler subprocess can connect to PostgreSQL.
    # These are read via os.getenv() in MediaCrawler's config/db_config.py.
    # pydantic-settings loads .env into its Settings object but NOT into
    # os.environ, so we must explicitly inject them for the subprocess.
    mc_db_env = {
        "POSTGRES_DB_HOST": _extract_db_param(settings.DATABASE_URL, "host", "localhost"),
        "POSTGRES_DB_PORT": _extract_db_param(settings.DATABASE_URL, "port", "5432"),
        "POSTGRES_DB_USER": _extract_db_param(settings.DATABASE_URL, "user", "postgres"),
        "POSTGRES_DB_PWD": _extract_db_param(settings.DATABASE_URL, "password", "123456"),
        "POSTGRES_DB_NAME": _extract_db_param(settings.DATABASE_URL, "database", "media_crawler"),
    }
    env.update(mc_db_env)
    return env


def _extract_db_param(url: str, param: str, default: str) -> str:
    """Extract a parameter from a SQLAlchemy-style database URL."""
    # e.g. postgresql+asyncpg://postgres:123456@localhost:5433/media_crawler
    try:
        if param == "user":
            return url.split("://")[1].split(":")[0]
        elif param == "password":
            return url.split("://")[1].split(":")[1].split("@")[0]
        elif param == "host":
            return url.split("@")[1].split(":")[0]
        elif param == "port":
            return url.split("://")[1].split("@")[1].split("/")[0].split(":")[-1]
        elif param == "database":
            return url.split("/")[-1]
    except (IndexError, ValueError):
        pass
    return default
