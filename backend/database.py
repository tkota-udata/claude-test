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
                created_at TEXT NOT NULL,
                likes INTEGER,
                retweets INTEGER,
                replies INTEGER,
                metrics_fetched_at TEXT
            )
        """)
        # Migrate: add metrics columns if missing
        for col, col_type in [("likes", "INTEGER"), ("retweets", "INTEGER"),
                               ("replies", "INTEGER"), ("metrics_fetched_at", "TEXT")]:
            try:
                await db.execute(f"ALTER TABLE scheduled_tweets ADD COLUMN {col} {col_type}")
            except Exception:
                pass

        await db.execute("""
            CREATE TABLE IF NOT EXISTS recurring_schedules (
                id TEXT PRIMARY KEY,
                goal TEXT NOT NULL,
                times_per_day INTEGER NOT NULL DEFAULT 2,
                start_hour INTEGER NOT NULL DEFAULT 8,
                end_hour INTEGER NOT NULL DEFAULT 22,
                enabled INTEGER NOT NULL DEFAULT 1,
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


async def get_top_tweets(limit: int = 5):
    """Get top performing tweets by engagement score."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT content, likes, retweets, replies,
               COALESCE(likes,0) + COALESCE(retweets,0)*2 + COALESCE(replies,0)*2 AS engagement_score
               FROM scheduled_tweets
               WHERE status='posted' AND metrics_fetched_at IS NOT NULL
               ORDER BY engagement_score DESC LIMIT ?""",
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


# Recurring schedule functions
async def insert_recurring_schedule(id: str, goal: str, times_per_day: int,
                                    start_hour: int, end_hour: int, created_at: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO recurring_schedules (id, goal, times_per_day, start_hour, end_hour, enabled, created_at) VALUES (?, ?, ?, ?, ?, 1, ?)",
            (id, goal, times_per_day, start_hour, end_hour, created_at),
        )
        await db.commit()


async def get_recurring_schedules():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM recurring_schedules ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_recurring_schedule(id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM recurring_schedules WHERE id=?", (id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def update_recurring_schedule_enabled(id: str, enabled: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE recurring_schedules SET enabled=? WHERE id=?",
            (1 if enabled else 0, id),
        )
        await db.commit()


async def delete_recurring_schedule(id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM recurring_schedules WHERE id=?", (id,))
        await db.commit()
