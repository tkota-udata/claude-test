import aiosqlite

DB_PATH = "tweets.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tweets (
                job_id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                scheduled_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'scheduled',
                tweet_id TEXT,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


async def insert_tweet(job_id: str, content: str, scheduled_at: str, created_at: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO scheduled_tweets (job_id, content, scheduled_at, status, created_at) VALUES (?, ?, ?, 'scheduled', ?)",
            (job_id, content, scheduled_at, created_at),
        )
        await db.commit()


async def get_scheduled_tweets():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM scheduled_tweets WHERE status = 'scheduled' ORDER BY scheduled_at"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def update_tweet_status(job_id: str, status: str, tweet_id: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE scheduled_tweets SET status = ?, tweet_id = ? WHERE job_id = ?",
            (status, tweet_id, job_id),
        )
        await db.commit()


async def get_tweet_by_job_id(job_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM scheduled_tweets WHERE job_id = ?", (job_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_pending_tweets():
    """Re-registers scheduled jobs on startup."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM scheduled_tweets WHERE status = 'scheduled'"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
