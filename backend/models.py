from pydantic import BaseModel
from typing import Optional


class GenerateRequest(BaseModel):
    goal: str
    context: str = ""
    count: int = 3


class TweetCandidate(BaseModel):
    id: str
    content: str
    char_count: int


class GenerateResponse(BaseModel):
    tweets: list[TweetCandidate]


class PostRequest(BaseModel):
    content: str


class PostResponse(BaseModel):
    tweet_id: str
    url: str
    posted_at: str


class ScheduleRequest(BaseModel):
    content: str
    scheduled_at: str  # ISO 8601 UTC


class ScheduledTweet(BaseModel):
    job_id: str
    content: str
    scheduled_at: str
    status: str


class ScheduleListResponse(BaseModel):
    scheduled: list[ScheduledTweet]


class CancelResponse(BaseModel):
    job_id: str
    status: str
