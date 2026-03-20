from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timezone
import sqlite3
import re

from config import settings

jobstores = {
    "default": SQLAlchemyJobStore(url=settings.database_url)
}

scheduler = BackgroundScheduler(jobstores=jobstores)


def _db_path() -> str:
    """Extract file path from SQLite URL."""
    path = re.sub(r"^sqlite:///", "", settings.database_url)
    return path


def _update_status_sync(job_id: str, status: str, tweet_id: str = None):
    """Synchronous DB update safe to call from APScheduler background threads."""
    conn = sqlite3.connect(_db_path())
    try:
        conn.execute(
            "UPDATE scheduled_tweets SET status = ?, tweet_id = ? WHERE job_id = ?",
            (status, tweet_id, job_id),
        )
        conn.commit()
    finally:
        conn.close()


def _post_scheduled_tweet(job_id: str, content: str):
    """Executed by APScheduler at the scheduled time."""
    from twitter import post_tweet

    try:
        result = post_tweet(content)
        _update_status_sync(job_id, "posted", result["tweet_id"])
    except Exception as e:
        _update_status_sync(job_id, "failed")
        raise e


def add_scheduled_job(job_id: str, content: str, run_at: datetime):
    scheduler.add_job(
        _post_scheduled_tweet,
        trigger=DateTrigger(run_date=run_at),
        args=[job_id, content],
        id=job_id,
        replace_existing=True,
    )


def remove_job(job_id: str):
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass


async def restore_jobs():
    """Re-register pending jobs from DB after restart."""
    from database import get_pending_tweets

    rows = await get_pending_tweets()
    now = datetime.now(timezone.utc)
    for row in rows:
        run_at = datetime.fromisoformat(row["scheduled_at"])
        if run_at.tzinfo is None:
            run_at = run_at.replace(tzinfo=timezone.utc)
        if run_at > now:
            try:
                add_scheduled_job(row["job_id"], row["content"], run_at)
            except Exception:
                pass
        else:
            # Past-due: try to post immediately instead of marking as failed
            from twitter import post_tweet
            from database import update_tweet_status
            try:
                result = post_tweet(row["content"])
                await update_tweet_status(row["job_id"], "posted", result["tweet_id"])
            except Exception:
                await update_tweet_status(row["job_id"], "failed")
