from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from scheduler import scheduler, restore_jobs, restore_recurring_jobs
from routes.tweets import router as tweets_router
from routes.schedule import router as schedule_router
from routes.autopost import router as autopost_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    scheduler.start()
    await restore_jobs()
    await restore_recurring_jobs()
    yield
    scheduler.shutdown()


app = FastAPI(title="X Post Automation API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin] if settings.cors_origin != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tweets_router, prefix="/api/v1")
app.include_router(schedule_router, prefix="/api/v1")
app.include_router(autopost_router, prefix="/api/v1")


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
