"""Monitoring scheduler for automated data collection."""

import asyncio
from datetime import datetime
from typing import Callable, Coroutine

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.config import get_settings

logger = structlog.get_logger()


class MonitoringScheduler:
    """Scheduler for automated monitoring tasks using APScheduler."""

    def __init__(self) -> None:
        """Initialize the monitoring scheduler."""
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler()
        self._is_running = False
        self._monitor_job_id = "github_monitor_job"

    def start(self) -> None:
        """Start the scheduler."""
        if self._is_running:
            logger.warning("scheduler_already_running")
            return

        self.scheduler.start()
        self._is_running = True
        logger.info("scheduler_started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if not self._is_running:
            return

        self.scheduler.shutdown(wait=True)
        self._is_running = False
        logger.info("scheduler_stopped")

    def add_interval_job(
        self,
        job_func: Callable[[], Coroutine],
        job_id: str,
        *,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        start_date: datetime | None = None,
        replace_existing: bool = True,
    ) -> None:
        """Add a job that runs at fixed intervals.

        Args:
            job_func: Async function to execute.
            job_id: Unique job identifier.
            seconds: Interval in seconds.
            minutes: Interval in minutes.
            hours: Interval in hours.
            start_date: Optional start date for the job.
            replace_existing: Replace existing job with same ID.
        """
        trigger = IntervalTrigger(
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            start_date=start_date,
        )

        self.scheduler.add_job(
            job_func,
            trigger=trigger,
            id=job_id,
            replace_existing=replace_existing,
            misfire_grace_time=300,  # 5 minutes grace period
        )

        logger.info(
            "interval_job_added",
            job_id=job_id,
            interval_seconds=seconds + minutes * 60 + hours * 3600,
        )

    def add_cron_job(
        self,
        job_func: Callable[[], Coroutine],
        job_id: str,
        *,
        hour: int | str = "*",
        minute: int | str = "*",
        day_of_week: int | str = "*",
        replace_existing: bool = True,
    ) -> None:
        """Add a job that runs on a cron schedule.

        Args:
            job_func: Async function to execute.
            job_id: Unique job identifier.
            hour: Hour to run (0-23 or cron expression).
            minute: Minute to run (0-59 or cron expression).
            day_of_week: Day of week (0-6 or cron expression).
            replace_existing: Replace existing job with same ID.
        """
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            day_of_week=day_of_week,
        )

        self.scheduler.add_job(
            job_func,
            trigger=trigger,
            id=job_id,
            replace_existing=replace_existing,
            misfire_grace_time=300,
        )

        logger.info(
            "cron_job_added",
            job_id=job_id,
            hour=hour,
            minute=minute,
            day_of_week=day_of_week,
        )

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job.

        Args:
            job_id: Job identifier to remove.

        Returns:
            True if job was removed, False if not found.
        """
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info("job_removed", job_id=job_id)
            return True
        return False

    def get_jobs(self) -> list[dict]:
        """Get list of all scheduled jobs.

        Returns:
            List of job information dictionaries.
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "next_run": job.next_run_time,
                "trigger": str(job.trigger),
            })
        return jobs

    def pause_job(self, job_id: str) -> bool:
        """Pause a scheduled job.

        Args:
            job_id: Job identifier to pause.

        Returns:
            True if job was paused, False if not found.
        """
        if self.scheduler.get_job(job_id):
            self.scheduler.pause_job(job_id)
            logger.info("job_paused", job_id=job_id)
            return True
        return False

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job.

        Args:
            job_id: Job identifier to resume.

        Returns:
            True if job was resumed, False if not found.
        """
        if self.scheduler.get_job(job_id):
            self.scheduler.resume_job(job_id)
            logger.info("job_resumed", job_id=job_id)
            return True
        return False

    def trigger_job_now(self, job_id: str) -> bool:
        """Trigger a job to run immediately.

        Args:
            job_id: Job identifier to trigger.

        Returns:
            True if job was triggered, False if not found.
        """
        if self.scheduler.get_job(job_id):
            self.scheduler.modify_job(job_id, next_run_time=datetime.now())
            logger.info("job_triggered", job_id=job_id)
            return True
        return False

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._is_running


# Global scheduler instance
_scheduler: MonitoringScheduler | None = None


def get_scheduler() -> MonitoringScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = MonitoringScheduler()
    return _scheduler
