import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from models import ScheduleRequest, ScheduledTweet, ScheduleListResponse, CancelResponse

router = APIRouter(prefix="/schedule")


@router.post("", response_model=ScheduledTweet)
async def schedule_tweet(req: ScheduleRequest):
    from database import insert_tweet
    from scheduler import add_scheduled_job

    if not req.content.strip():
        raise HTTPException(status_code=400, detail="content is required")
    if len(req.content) > 280:
        raise HTTPException(status_code=400, detail="content exceeds 280 characters")

    try:
        run_at = datetime.fromisoformat(req.scheduled_at)
        if run_at.tzinfo is None:
            run_at = run_at.replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="scheduled_at must be ISO 8601 format")

    if run_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="scheduled_at must be in the future")

    job_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    await insert_tweet(job_id, req.content, run_at.isoformat(), created_at)
    add_scheduled_job(job_id, req.content, run_at)

    return ScheduledTweet(
        job_id=job_id,
        content=req.content,
        scheduled_at=run_at.isoformat(),
        status="scheduled",
    )


@router.get("", response_model=ScheduleListResponse)
async def list_scheduled():
    from database import get_scheduled_tweets

    rows = await get_scheduled_tweets()
    return ScheduleListResponse(
        scheduled=[
            ScheduledTweet(
                job_id=r["job_id"],
                content=r["content"],
                scheduled_at=r["scheduled_at"],
                status=r["status"],
            )
            for r in rows
        ]
    )


@router.delete("/{job_id}", response_model=CancelResponse)
async def cancel_tweet(job_id: str):
    from database import update_tweet_status
    from scheduler import remove_job

    remove_job(job_id)
    await update_tweet_status(job_id, "cancelled")
    return CancelResponse(job_id=job_id, status="cancelled")
