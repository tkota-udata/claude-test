from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timezone
import asyncio

from config import settings

jobstores = {
    "default": SQLAlchemyJobStore(url=settings.database_url)
}

scheduler = BackgroundScheduler(jobstores=jobstores)


def _post_scheduled_tweet(job_id: str, content: str):
    """Executed by APScheduler at the scheduled time."""
    from twitter import post_tweet
    from database import update_tweet_status

    try:
        result = post_tweet(content)
        asyncio.run(update_tweet_status(job_id, "posted", result["tweet_id"]))
    except Exception as e:
        asyncio.run(update_tweet_status(job_id, "failed"))
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
            # Past-due: mark as failed
            from database import update_tweet_status
            await update_tweet_status(row["job_id"], "failed")
