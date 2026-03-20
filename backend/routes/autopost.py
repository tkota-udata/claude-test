import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from models import (AutoPostRequest, AutoPostSchedule, AutoPostListResponse,
                    ToggleRequest, AnalyticsResponse)

router = APIRouter(prefix="/autopost")


@router.post("", response_model=AutoPostSchedule)
async def create_autopost(req: AutoPostRequest):
    from database import insert_recurring_schedule
    from scheduler import add_recurring_jobs

    if not req.goal.strip():
        raise HTTPException(status_code=400, detail="goal is required")
    if not (1 <= req.times_per_day <= 5):
        raise HTTPException(status_code=400, detail="times_per_day must be 1-5")
    if req.start_hour >= req.end_hour:
        raise HTTPException(status_code=400, detail="start_hour must be less than end_hour")

    schedule_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    await insert_recurring_schedule(schedule_id, req.goal, req.times_per_day,
                                    req.start_hour, req.end_hour, created_at)
    add_recurring_jobs(schedule_id, req.goal, req.times_per_day, req.start_hour, req.end_hour)

    return AutoPostSchedule(
        id=schedule_id, goal=req.goal, times_per_day=req.times_per_day,
        start_hour=req.start_hour, end_hour=req.end_hour,
        enabled=True, created_at=created_at,
    )


@router.get("", response_model=AutoPostListResponse)
async def list_autoposts():
    from database import get_recurring_schedules
    rows = await get_recurring_schedules()
    return AutoPostListResponse(
        schedules=[
            AutoPostSchedule(
                id=r["id"], goal=r["goal"], times_per_day=r["times_per_day"],
                start_hour=r["start_hour"], end_hour=r["end_hour"],
                enabled=bool(r["enabled"]), created_at=r["created_at"],
            )
            for r in rows
        ]
    )


@router.patch("/{schedule_id}/toggle", response_model=AutoPostSchedule)
async def toggle_autopost(schedule_id: str, req: ToggleRequest):
    from database import get_recurring_schedule, update_recurring_schedule_enabled
    from scheduler import add_recurring_jobs, remove_recurring_jobs

    row = await get_recurring_schedule(schedule_id)
    if not row:
        raise HTTPException(status_code=404, detail="schedule not found")

    await update_recurring_schedule_enabled(schedule_id, req.enabled)
    if req.enabled:
        add_recurring_jobs(schedule_id, row["goal"], row["times_per_day"],
                           row["start_hour"], row["end_hour"])
    else:
        remove_recurring_jobs(schedule_id)

    return AutoPostSchedule(
        id=schedule_id, goal=row["goal"], times_per_day=row["times_per_day"],
        start_hour=row["start_hour"], end_hour=row["end_hour"],
        enabled=req.enabled, created_at=row["created_at"],
    )


@router.delete("/{schedule_id}")
async def delete_autopost(schedule_id: str):
    from database import get_recurring_schedule, delete_recurring_schedule
    from scheduler import remove_recurring_jobs

    row = await get_recurring_schedule(schedule_id)
    if not row:
        raise HTTPException(status_code=404, detail="schedule not found")

    remove_recurring_jobs(schedule_id)
    await delete_recurring_schedule(schedule_id)
    return {"id": schedule_id, "status": "deleted"}


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics():
    from database import get_top_tweets
    from twitter import get_follower_count

    top_tweets = await get_top_tweets(5)
    try:
        follower_count = get_follower_count()
    except Exception:
        follower_count = 0

    return AnalyticsResponse(top_tweets=top_tweets, follower_count=follower_count)
