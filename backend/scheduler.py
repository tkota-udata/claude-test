from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone, timedelta
import sqlite3
import re
import logging

from config import settings

jobstores = {
    "default": SQLAlchemyJobStore(url=settings.database_url)
}

scheduler = BackgroundScheduler(jobstores=jobstores)


def _db_path() -> str:
    path = re.sub(r"^sqlite:///", "", settings.database_url)
    return path


def _update_status_sync(job_id: str, status: str, tweet_id: str = None):
    conn = sqlite3.connect(_db_path())
    try:
        conn.execute(
            "UPDATE scheduled_tweets SET status = ?, tweet_id = ? WHERE job_id = ?",
            (status, tweet_id, job_id),
        )
        conn.commit()
    finally:
        conn.close()


def _schedule_metrics_fetch(job_id: str, tweet_id: str):
    """Schedule metrics fetch 24 hours after posting."""
    fetch_at = datetime.now(timezone.utc) + timedelta(hours=24)
    try:
        scheduler.add_job(
            _fetch_tweet_metrics,
            trigger=DateTrigger(run_date=fetch_at),
            args=[job_id, tweet_id],
            id=f"metrics_{job_id}",
            replace_existing=True,
        )
    except Exception as e:
        logging.warning(f"Failed to schedule metrics fetch for {job_id}: {e}")


def _fetch_tweet_metrics(job_id: str, tweet_id: str):
    """Fetch and store public metrics for a posted tweet."""
    from twitter import get_tweet_metrics
    try:
        metrics = get_tweet_metrics(tweet_id)
        fetched_at = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(_db_path())
        try:
            conn.execute(
                "UPDATE scheduled_tweets SET likes=?, retweets=?, replies=?, metrics_fetched_at=? WHERE job_id=?",
                (metrics["likes"], metrics["retweets"], metrics["replies"], fetched_at, job_id),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logging.error(f"Metrics fetch failed for tweet {tweet_id}: {e}")


def _post_scheduled_tweet(job_id: str, content: str):
    """Executed by APScheduler at the scheduled time."""
    from twitter import post_tweet
    try:
        result = post_tweet(content)
        _update_status_sync(job_id, "posted", result["tweet_id"])
        _schedule_metrics_fetch(job_id, result["tweet_id"])
    except Exception as e:
        _update_status_sync(job_id, "failed")
        raise e


def _calc_posting_hours(times_per_day: int, start_hour: int, end_hour: int) -> list:
    """Calculate evenly distributed posting hours within the window."""
    if times_per_day == 1:
        return [start_hour]
    interval = (end_hour - start_hour) / times_per_day
    return [int(start_hour + i * interval) for i in range(times_per_day)]


def _auto_generate_and_post(schedule_id: str, goal: str):
    """Auto-generate a tweet from the goal and post it immediately."""
    import uuid
    from twitter import post_tweet
    from ai import generate_tweets

    db_path = _db_path()

    # Fetch top-performing tweets for feedback context
    top_tweets = []
    try:
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.execute(
                """SELECT content, likes, retweets, replies,
                   COALESCE(likes,0) + COALESCE(retweets,0)*2 + COALESCE(replies,0)*2 AS engagement_score
                   FROM scheduled_tweets
                   WHERE status='posted' AND metrics_fetched_at IS NOT NULL
                   ORDER BY engagement_score DESC LIMIT 3"""
            )
            cols = [c[0] for c in cursor.description]
            top_tweets = [dict(zip(cols, row)) for row in cursor.fetchall()]
        finally:
            conn.close()
    except Exception:
        pass

    try:
        tweets = generate_tweets(goal, "", 1, performance_context=top_tweets or None)
        if not tweets:
            raise ValueError("No tweets generated")
        content = tweets[0]
        result = post_tweet(content)

        job_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                "INSERT INTO scheduled_tweets (job_id, content, scheduled_at, status, tweet_id, created_at) VALUES (?, ?, ?, 'posted', ?, ?)",
                (job_id, content, created_at, result["tweet_id"], created_at),
            )
            conn.commit()
        finally:
            conn.close()

        _schedule_metrics_fetch(job_id, result["tweet_id"])
        logging.info(f"Auto-post succeeded for schedule {schedule_id}: {result['tweet_id']}")
    except Exception as e:
        logging.error(f"Auto-post failed for schedule {schedule_id}: {e}")


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


def add_recurring_jobs(schedule_id: str, goal: str, times_per_day: int,
                       start_hour: int, end_hour: int):
    """Register CronTrigger jobs for a recurring auto-post schedule."""
    hours = _calc_posting_hours(times_per_day, start_hour, end_hour)
    for i, hour in enumerate(hours):
        scheduler.add_job(
            _auto_generate_and_post,
            trigger=CronTrigger(hour=hour, minute=0),
            args=[schedule_id, goal],
            id=f"recurring_{schedule_id}_{i}",
            replace_existing=True,
        )


def remove_recurring_jobs(schedule_id: str, max_slots: int = 5):
    """Remove all recurring jobs for a schedule."""
    for i in range(max_slots):
        try:
            scheduler.remove_job(f"recurring_{schedule_id}_{i}")
        except Exception:
            pass


async def restore_jobs():
    """Re-register pending one-off jobs from DB after restart."""
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
            from twitter import post_tweet
            from database import update_tweet_status
            try:
                result = post_tweet(row["content"])
                await update_tweet_status(row["job_id"], "posted", result["tweet_id"])
                _schedule_metrics_fetch(row["job_id"], result["tweet_id"])
            except Exception:
                await update_tweet_status(row["job_id"], "failed")


async def restore_recurring_jobs():
    """Re-register recurring auto-post jobs from DB after restart."""
    from database import get_recurring_schedules

    rows = await get_recurring_schedules()
    for row in rows:
        if row["enabled"]:
            try:
                add_recurring_jobs(row["id"], row["goal"], row["times_per_day"],
                                   row["start_hour"], row["end_hour"])
            except Exception as e:
                logging.warning(f"Failed to restore recurring job {row['id']}: {e}")
